"""Business rules for volunteer departure interviews."""

from dataclasses import dataclass
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
from app.modules.recruitment.schemas.commands import DepartureInterviewWrite
from app.modules.recruitment.schemas.departures import DepartureFieldDraft
from app.modules.recruitment.services.form_fields import (
    ConfigurableFormFieldService,
    FieldSaveErrors,
)


@dataclass(frozen=True)
class DepartureAnswerField:
    key: str
    label: str
    field_type: str
    required: bool
    placeholder: str
    options: list[str]


class DepartureService(
    ConfigurableFormFieldService[DepartureField, DepartureFieldDraft]
):
    def __init__(self, session: Session):
        self.session = session
        self.repo = DepartureRepository(session)
        super().__init__(
            self.repo,
            defaults=DEFAULT_DEPARTURE_FIELDS,
            errors=FieldSaveErrors(
                unknown_field="Nie znaleziono pola ankiety odejścia",
                missing_system_field="Nie można usunąć podstawowych pól ankiety",
                invalid_system_field=(
                    "Podstawowe pola muszą zachować typ, wymagalność i aktywność"
                ),
            ),
        )

    def _validate_answers(self, answers: dict[str, Any]) -> list[dict[str, Any]]:
        fields = [
            DepartureAnswerField(
                key=field.key,
                label=field.label,
                field_type=field.field_type,
                required=field.required,
                placeholder=field.placeholder,
                options=list(field.options),
            )
            for field in self.list_fields(active_only=True)
        ]
        return self._validate_field_answers(fields, answers)

    def _validate_snapshot_answers(
        self, fields: list[dict[str, Any]], answers: dict[str, Any]
    ) -> list[dict[str, Any]]:
        definitions = [
            DepartureAnswerField(
                key=str(field["key"]),
                label=str(field["label"]),
                field_type=str(field["field_type"]),
                required=bool(field.get("required", False)),
                placeholder=str(field.get("placeholder", "")),
                options=list(field.get("options", [])),
            )
            for field in fields
        ]
        return self._validate_field_answers(definitions, answers)

    @staticmethod
    def _validate_field_answers(
        fields: list[DepartureAnswerField], answers: dict[str, Any]
    ) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for field in fields:
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
                    "options": field.options,
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
                DepartureInterviewWrite(
                    volunteer_id=volunteer_id,
                    departure_date=departure_date,
                    departure_reason=reason,
                    stay_in_contact=bool(indexed.get("stay_in_contact")),
                    answers=validated,
                    completed_by_id=completed_by_id,
                )
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
