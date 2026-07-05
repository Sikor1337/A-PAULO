"""Business rules for volunteer departure interviews."""

import re
import unicodedata
from datetime import date
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import ConflictError, NotFoundError, ValidationException
from app.modules.core_data.models import User
from app.modules.recruitment.departure_constants import (
    DEFAULT_DEPARTURE_FIELDS,
    DEPARTURE_CHOICE_TYPES,
)
from app.modules.recruitment.models import DepartureField, DepartureInterview
from app.modules.recruitment.repositories.departures import DepartureRepository
from app.modules.recruitment.schemas.departures import DepartureFieldDraft


def _slugify(value: str) -> str:
    normalized = (
        unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode().lower()
    )
    return re.sub(r"[^a-z0-9]+", "_", normalized).strip("_") or "pytanie"


class DepartureService:
    def __init__(self, session: Session):
        self.session = session
        self.repo = DepartureRepository(session)

    def _ensure_default_fields(self) -> None:
        current = self.repo.list_fields()
        defaults = (
            DEFAULT_DEPARTURE_FIELDS
            if not current
            else [values for values in DEFAULT_DEPARTURE_FIELDS if values["is_system"]]
        )
        by_key = {field.key: field for field in current}
        changed = False

        for values in defaults:
            field = by_key.get(values["key"])
            if field is None:
                field = self.repo.create_field(
                    position=0,
                    options=[],
                    is_active=True,
                    **values,
                )
                by_key[values["key"]] = field
                changed = True
                continue

            if values["is_system"]:
                protected_values = {
                    "field_type": values["field_type"],
                    "required": values["required"],
                    "is_active": True,
                    "is_system": True,
                }
                for attribute, expected in protected_values.items():
                    if getattr(field, attribute) != expected:
                        setattr(field, attribute, expected)
                        changed = True

        if not changed:
            return

        system_keys = [
            values["key"] for values in DEFAULT_DEPARTURE_FIELDS if values["is_system"]
        ]
        ordered = [by_key[key] for key in system_keys]
        if current:
            ordered.extend(field for field in current if field.key not in system_keys)
        else:
            ordered.extend(
                by_key[values["key"]]
                for values in DEFAULT_DEPARTURE_FIELDS
                if not values["is_system"]
            )
        for position, field in enumerate(ordered):
            if field.position != position:
                field.position = position

        self.repo.commit(skip_audit=True)

    def list_fields(self, *, active_only: bool = False) -> list[DepartureField]:
        self._ensure_default_fields()
        return self.repo.list_fields(active_only=active_only)

    def save_fields(self, drafts: list[DepartureFieldDraft]) -> list[DepartureField]:
        try:
            current = self.list_fields()
            by_id = {field.id: field for field in current}
            submitted_ids = {draft.id for draft in drafts if draft.id is not None}
            if submitted_ids - set(by_id):
                raise NotFoundError("Nie znaleziono pola ankiety odejścia")
            system_ids = {field.id for field in current if field.is_system}
            if not system_ids.issubset(submitted_ids):
                raise ConflictError("Nie można usunąć podstawowych pól ankiety")

            keys = {field.key for field in current}
            for position, draft in enumerate(drafts):
                if draft.id is None:
                    key = base = _slugify(draft.label)
                    suffix = 2
                    while key in keys:
                        key = f"{base}_{suffix}"
                        suffix += 1
                    keys.add(key)
                    self.repo.create_field(
                        key=key,
                        position=position,
                        is_system=False,
                        **draft.model_dump(exclude={"id"}),
                    )
                    continue
                field = by_id[draft.id]
                if field.is_system and (
                    draft.field_type != field.field_type
                    or draft.required != field.required
                    or not draft.is_active
                ):
                    raise ConflictError(
                        "Podstawowe pola muszą zachować typ, wymagalność i aktywność"
                    )
                for key, value in draft.model_dump(exclude={"id"}).items():
                    setattr(field, key, value)
                field.position = position
            for field in current:
                if field.id not in submitted_ids:
                    self.repo.delete_field(field)
            self.repo.commit(skip_audit=True)
            return self.repo.list_fields()
        except Exception:
            self.session.rollback()
            raise

    def _validate_answers(self, answers: dict[str, Any]) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for field in self.list_fields(active_only=True):
            value = answers.get(field.key)
            if field.field_type == "checkbox":
                if value is not None and not isinstance(value, bool):
                    raise ValidationException(f"Nieprawidłowa odpowiedź: {field.label}")
            elif field.field_type == "multiselect":
                if value is not None and (
                    not isinstance(value, list)
                    or any(not isinstance(item, str) for item in value)
                    or len(value) != len(set(value))
                ):
                    raise ValidationException(f"Nieprawidłowa odpowiedź: {field.label}")
            elif value is not None and not isinstance(value, str):
                raise ValidationException(f"Pole „{field.label}” musi zawierać tekst")
            if isinstance(value, str):
                value = value.strip()
                if len(value) > 10_000:
                    raise ValidationException(
                        f"Odpowiedź jest zbyt długa: {field.label}"
                    )
            empty = value is None or value == "" or value == []
            if field.required and empty:
                raise ValidationException(f"Pole „{field.label}” jest wymagane")
            if field.field_type in DEPARTURE_CHOICE_TYPES and not empty:
                selected = value if isinstance(value, list) else [value]
                if any(item not in field.options for item in selected):
                    raise ValidationException(f"Nieprawidłowa odpowiedź: {field.label}")
            if field.field_type == "date" and not empty:
                try:
                    date.fromisoformat(str(value))
                except ValueError as error:
                    raise ValidationException(
                        f"Nieprawidłowa data: {field.label}"
                    ) from error
            result.append(
                {
                    "key": field.key,
                    "label": field.label,
                    "field_type": field.field_type,
                    "required": field.required,
                    "placeholder": field.placeholder,
                    "options": list(field.options),
                    "value": value,
                }
            )
        return result

    def _validate_snapshot_answers(
        self, fields: list[dict[str, Any]], answers: dict[str, Any]
    ) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for field in fields:
            key = str(field["key"])
            label = str(field["label"])
            field_type = str(field["field_type"])
            required = bool(field.get("required", False))
            placeholder = str(field.get("placeholder", ""))
            options = list(field.get("options", []))
            value = answers.get(key)
            if field_type == "checkbox":
                if value is not None and not isinstance(value, bool):
                    raise ValidationException(f"Nieprawidłowa odpowiedź: {label}")
            elif field_type == "multiselect":
                if value is not None and (
                    not isinstance(value, list)
                    or any(not isinstance(item, str) for item in value)
                    or len(value) != len(set(value))
                ):
                    raise ValidationException(f"Nieprawidłowa odpowiedź: {label}")
            elif value is not None and not isinstance(value, str):
                raise ValidationException(f"Pole „{label}” musi zawierać tekst")
            if isinstance(value, str):
                value = value.strip()
                if len(value) > 10_000:
                    raise ValidationException(f"Odpowiedź jest zbyt długa: {label}")
            empty = value is None or value == "" or value == []
            if required and empty:
                raise ValidationException(f"Pole „{label}” jest wymagane")
            if field_type in DEPARTURE_CHOICE_TYPES and not empty:
                selected = value if isinstance(value, list) else [value]
                if any(item not in options for item in selected):
                    raise ValidationException(f"Nieprawidłowa odpowiedź: {label}")
            if field_type == "date" and not empty:
                try:
                    date.fromisoformat(str(value))
                except ValueError as error:
                    raise ValidationException(f"Nieprawidłowa data: {label}") from error
            result.append(
                {
                    "key": key,
                    "label": label,
                    "field_type": field_type,
                    "required": required,
                    "placeholder": placeholder,
                    "options": options,
                    "value": value,
                }
            )
        return result

    def create_interview(
        self, volunteer_id: int, answers: dict[str, Any], completed_by_id: int
    ) -> DepartureInterview:
        try:
            volunteer = self.repo.get_volunteer(volunteer_id)
            if not volunteer:
                raise NotFoundError("Nie znaleziono wolontariusza")
            if self.repo.get_by_volunteer(volunteer_id):
                raise ConflictError("Ankieta odejścia tego wolontariusza już istnieje")
            validated = self._validate_answers(answers)
            indexed = {answer["key"]: answer["value"] for answer in validated}
            departure_date = date.fromisoformat(str(indexed["departure_date"]))
            reason = str(indexed["departure_reason"])
            interview = self.repo.create(
                volunteer_id=volunteer_id,
                departure_date=departure_date,
                departure_reason=reason,
                stay_in_contact=bool(indexed.get("stay_in_contact")),
                answers=validated,
                completed_by_id=completed_by_id,
            )
            self.repo.commit(skip_audit=True)
            return self.get_interview(interview.id)
        except IntegrityError as error:
            self.session.rollback()
            raise ConflictError("Ankieta odejścia już istnieje") from error
        except Exception:
            self.session.rollback()
            raise

    def get_self_service(self, user: User) -> dict:
        volunteer = self.repo.get_volunteer_for_user(user.id, user.email)
        if volunteer is None:
            raise NotFoundError("Brak profilu wolontariusza powiązanego z tym kontem")
        return {
            "volunteer": volunteer,
            "fields": self.list_fields(active_only=True),
            "interview": self.repo.get_by_volunteer(volunteer.id),
        }

    def create_self_interview(
        self, user: User, answers: dict[str, Any]
    ) -> DepartureInterview:
        volunteer = self.repo.get_volunteer_for_user(user.id, user.email)
        if volunteer is None:
            raise NotFoundError("Brak profilu wolontariusza powiązanego z tym kontem")
        return self.create_interview(volunteer.id, answers, user.id)

    def update_self_interview(
        self, user: User, answers: dict[str, Any]
    ) -> DepartureInterview:
        volunteer = self.repo.get_volunteer_for_user(user.id, user.email)
        if volunteer is None:
            raise NotFoundError("Brak profilu wolontariusza powiązanego z tym kontem")
        interview = self.repo.get_by_volunteer(volunteer.id)
        if interview is None:
            raise NotFoundError("Ankieta odejścia nie została jeszcze wypełniona")
        try:
            validated = self._validate_snapshot_answers(interview.answers, answers)
            indexed = {answer["key"]: answer["value"] for answer in validated}
            interview.departure_date = date.fromisoformat(
                str(indexed["departure_date"])
            )
            interview.departure_reason = str(indexed["departure_reason"])
            interview.stay_in_contact = bool(indexed.get("stay_in_contact"))
            interview.answers = validated
            self.repo.commit(skip_audit=True)
            return self.get_interview(interview.id)
        except Exception:
            self.session.rollback()
            raise

    def list_interviews(self, *, skip: int, limit: int) -> list[DepartureInterview]:
        return self.repo.list(skip=skip, limit=limit)

    def get_interview(self, interview_id: int) -> DepartureInterview:
        interview = self.repo.get(interview_id)
        if not interview:
            raise NotFoundError("Nie znaleziono ankiety odejścia")
        return interview
