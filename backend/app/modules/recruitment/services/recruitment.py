"""Business rules for configurable forms and candidate onboarding."""

import json
import re
import secrets
import unicodedata
from datetime import UTC, date, datetime
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import ConflictError, NotFoundError, ValidationException
from app.modules.pi.models.volunteer import Volunteer
from app.modules.recruitment.models import RecruitmentField, RecruitmentSubmission
from app.modules.recruitment.repositories import RecruitmentRepository

DEFAULT_FIELDS = [
    {
        "key": "full_name",
        "label": "Imię i nazwisko",
        "field_type": "text",
        "required": True,
        "placeholder": "np. Jan Kowalski",
        "is_system": True,
    },
    {
        "key": "email",
        "label": "Adres e-mail",
        "field_type": "email",
        "required": True,
        "placeholder": "email@example.com",
        "is_system": True,
    },
    {
        "key": "phone",
        "label": "Telefon",
        "field_type": "tel",
        "required": True,
        "placeholder": "+48 123 456 789",
        "is_system": True,
    },
    {
        "key": "social_link",
        "label": "Link do profilu społecznościowego",
        "field_type": "text",
        "required": False,
        "placeholder": "https://...",
        "is_system": False,
    },
    {
        "key": "availability",
        "label": "Dyspozycyjność",
        "field_type": "textarea",
        "required": False,
        "placeholder": "Napisz, w jakie dni i godziny jesteś dostępny/a",
        "is_system": False,
    },
]
ALLOWED_TYPES = {
    "text",
    "textarea",
    "email",
    "tel",
    "date",
    "select",
    "radio",
    "checkbox",
}
CHOICE_TYPES = {"select", "radio"}
VALID_STATUSES = {"SUBMITTED", "ONBOARDING", "ACCEPTED", "REJECTED", "RETURNED"}


def _slugify(value: str) -> str:
    normalized = (
        unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode().lower()
    )
    return re.sub(r"[^a-z0-9]+", "_", normalized).strip("_") or "pytanie"


class RecruitmentService:
    def __init__(self, session: Session):
        self.session = session
        self.repo = RecruitmentRepository(session)

    def _ensure_default_fields(self) -> None:
        if self.repo.list_fields():
            return
        for position, values in enumerate(DEFAULT_FIELDS):
            self.repo.create_field(
                position=position, options=[], is_active=True, **values
            )
        self.session.commit()

    def list_fields(self, *, active_only: bool = False) -> list[RecruitmentField]:
        self._ensure_default_fields()
        return self.repo.list_fields(active_only=active_only)

    def create_field(self, **values) -> RecruitmentField:
        try:
            label = values["label"].strip()
            if not label:
                raise ValidationException("Treść pytania nie może być pusta")
            field_type = values.get("field_type", "text")
            options = [
                str(option).strip()
                for option in values.get("options", [])
                if str(option).strip()
            ]
            self._validate_field(field_type, options)
            existing_keys = {field.key for field in self.list_fields()}
            base_key = _slugify(label)
            key = base_key
            suffix = 2
            while key in existing_keys:
                key = f"{base_key}_{suffix}"
                suffix += 1
            position = values.get("position")
            if position is None:
                position = (
                    max(
                        (field.position for field in self.repo.list_fields()),
                        default=-1,
                    )
                    + 1
                )
            field = self.repo.create_field(
                key=key,
                label=label,
                field_type=field_type,
                required=values.get("required", False),
                placeholder=values.get("placeholder", "").strip(),
                options=options,
                position=position,
                is_active=True,
                is_system=False,
            )
            self.session.commit()
            self.session.refresh(field)
            return field
        except Exception:
            self.session.rollback()
            raise

    def reorder_fields(self, field_ids: list[int]) -> list[RecruitmentField]:
        try:
            fields = self.list_fields()
            existing_ids = {field.id for field in fields}
            if len(field_ids) != len(set(field_ids)) or set(field_ids) != existing_ids:
                raise ValidationException(
                    "Kolejność musi zawierać każde pole dokładnie raz"
                )
            by_id = {field.id: field for field in fields}
            for position, field_id in enumerate(field_ids):
                by_id[field_id].position = position
            self.session.commit()
            return self.repo.list_fields()
        except Exception:
            self.session.rollback()
            raise

    def update_field(self, field_id: int, **values) -> RecruitmentField:
        try:
            field = self._get_field(field_id)
            if any(value is None for value in values.values()):
                raise ValidationException("Pola edycji nie mogą mieć wartości null")
            if field.is_system:
                changes_contract = (
                    (
                        "field_type" in values
                        and values["field_type"] != field.field_type
                    )
                    or ("required" in values and values["required"] is not True)
                    or ("is_active" in values and values["is_active"] is not True)
                )
                if changes_contract:
                    raise ConflictError(
                        "Podstawowe pola kontaktowe muszą pozostać aktywne i wymagane"
                    )
            field_type = values.get("field_type", field.field_type)
            options = values.get("options", field.options)
            options = [str(option).strip() for option in options if str(option).strip()]
            self._validate_field(field_type, options)
            for key, value in values.items():
                if key == "options":
                    value = options
                if isinstance(value, str):
                    value = value.strip()
                setattr(field, key, value)
            self.session.commit()
            self.session.refresh(field)
            return field
        except Exception:
            self.session.rollback()
            raise

    def delete_field(self, field_id: int) -> None:
        try:
            field = self._get_field(field_id)
            if field.is_system:
                raise ConflictError("Nie można usunąć podstawowego pola formularza")
            self.repo.delete_field(field)
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise

    def create_invitation(
        self, recipient_name: str | None = None, recipient_email: str | None = None
    ):
        try:
            name = (recipient_name or "").strip() or None
            email = (recipient_email or "").strip().lower() or None
            if email and (
                self.repo.get_submission_by_email(email)
                or self.repo.get_active_invitation_by_email(email)
            ):
                raise ConflictError(
                    "Dla tego adresu e-mail istnieje już zaproszenie lub zgłoszenie"
                )
            token = secrets.token_urlsafe(32)
            while self.repo.get_invitation_by_token(token):
                token = secrets.token_urlsafe(32)
            invitation = self.repo.create_invitation(
                token=token,
                recipient_name=name,
                recipient_email=email,
                is_active=True,
            )
            self.session.commit()
            self.session.refresh(invitation)
            return invitation
        except Exception:
            self.session.rollback()
            raise

    def list_invitations(self, *, skip: int = 0, limit: int = 100):
        return self.repo.list_invitations(skip=skip, limit=limit)

    def revoke_invitation(self, invitation_id: int) -> None:
        try:
            invitation = self.repo.get_invitation(invitation_id)
            if not invitation:
                raise NotFoundError("Nie znaleziono zaproszenia")
            if invitation.submission:
                raise ConflictError("Nie można wyłączyć wykorzystanego zaproszenia")
            invitation.is_active = False
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise

    def get_public_invitation(self, token: str):
        invitation = self.repo.get_invitation_by_token(token)
        if not invitation or not invitation.is_active:
            raise NotFoundError("Link rekrutacyjny jest nieprawidłowy lub nieaktywny")
        if invitation.submission and invitation.submission.status != "RETURNED":
            raise ConflictError("Ten formularz został już wysłany")
        return invitation

    def submit(
        self, invitation_token: str, raw_answers: dict[str, Any]
    ) -> RecruitmentSubmission:
        try:
            invitation = self.get_public_invitation(invitation_token)
            fields = self.list_fields(active_only=True)
            answers = self._validate_answers(fields, raw_answers)
            indexed = {answer["key"]: answer["value"] for answer in answers}
            email = str(indexed["email"]).strip().lower()
            if invitation.recipient_email and email != invitation.recipient_email:
                raise ValidationException(
                    "Adres e-mail musi być zgodny z wystawionym zaproszeniem"
                )
            existing = invitation.submission
            email_submission = self.repo.get_submission_by_email(email)
            if email_submission and email_submission is not existing:
                raise ConflictError(
                    "Formularz dla tego adresu e-mail został już wysłany"
                )
            values = {
                "invitation_id": invitation.id,
                "full_name": str(indexed["full_name"]).strip(),
                "email": email,
                "phone": str(indexed["phone"]).strip(),
                "social_link": str(indexed.get("social_link") or "").strip(),
                "availability": str(indexed.get("availability") or "").strip(),
                "answers": answers,
                "status": "SUBMITTED",
                "submitted_at": datetime.now(UTC),
                "status_changed_at": datetime.now(UTC),
            }
            if existing:
                for key, value in values.items():
                    setattr(existing, key, value)
                submission = existing
            else:
                submission = self.repo.create_submission(**values)
            self.session.commit()
            self.session.refresh(submission)
            return submission
        except IntegrityError as error:
            self.session.rollback()
            raise ConflictError(
                "Formularz dla tego adresu e-mail został już wysłany"
            ) from error
        except Exception:
            self.session.rollback()
            raise

    def list_submissions(self, **filters) -> list[RecruitmentSubmission]:
        status = filters.get("status")
        if status and status not in VALID_STATUSES:
            raise ValidationException("Nieznany status zgłoszenia")
        return self.repo.list_submissions(**filters)

    def get_submission(self, submission_id: int) -> RecruitmentSubmission:
        submission = self.repo.get_submission(submission_id)
        if not submission:
            raise NotFoundError("Nie znaleziono zgłoszenia rekrutacyjnego")
        return submission

    def move_to_onboarding(self, submission_id: int) -> RecruitmentSubmission:
        return self._transition(submission_id, {"SUBMITTED"}, "ONBOARDING")

    def return_submission(
        self, submission_id: int, reason: str | None = None
    ) -> RecruitmentSubmission:
        try:
            submission = self.get_submission(submission_id)
            if submission.status not in {"SUBMITTED", "ONBOARDING"}:
                raise ConflictError(
                    "Ta zmiana statusu nie jest dostępna na obecnym etapie"
                )
            submission.status = "RETURNED"
            submission.return_reason = (reason or "").strip() or None
            submission.status_changed_at = datetime.now(UTC)
            self.session.commit()
            self.session.refresh(submission)
            return submission
        except Exception:
            self.session.rollback()
            raise

    def reject(self, submission_id: int) -> RecruitmentSubmission:
        return self._transition(submission_id, {"ONBOARDING"}, "REJECTED")

    def accept(self, submission_id: int) -> RecruitmentSubmission:
        try:
            submission = self.get_submission(submission_id)
            if submission.status != "ONBOARDING":
                raise ConflictError(
                    "Tylko osobę we wdrażaniu można oznaczyć jako wdrożoną"
                )
            if (
                self.session.query(Volunteer)
                .filter(Volunteer.email == submission.email)
                .first()
            ):
                raise ConflictError("Wolontariusz z tym adresem e-mail już istnieje")
            volunteer = Volunteer(
                full_name=submission.full_name,
                email=submission.email,
                phone=submission.phone,
                social_link=submission.social_link or None,
                status="Aktywny",
                join_date=datetime.now(UTC),
                notes="Utworzono po zakończeniu procesu rekrutacji.",
                history="Rekrutacja zakończona pomyślnie.",
            )
            self.session.add(volunteer)
            self.session.flush()
            submission.volunteer_id = volunteer.id
            submission.status = "ACCEPTED"
            submission.status_changed_at = datetime.now(UTC)
            self.session.commit()
            self.session.refresh(submission)
            return submission
        except Exception:
            self.session.rollback()
            raise

    def _transition(
        self, submission_id: int, allowed: set[str], target: str
    ) -> RecruitmentSubmission:
        try:
            submission = self.get_submission(submission_id)
            if submission.status not in allowed:
                raise ConflictError(
                    "Ta zmiana statusu nie jest dostępna na obecnym etapie"
                )
            submission.status = target
            submission.status_changed_at = datetime.now(UTC)
            self.session.commit()
            self.session.refresh(submission)
            return submission
        except Exception:
            self.session.rollback()
            raise

    def _get_field(self, field_id: int) -> RecruitmentField:
        field = self.repo.get_field(field_id)
        if not field:
            raise NotFoundError("Nie znaleziono pola formularza")
        return field

    @staticmethod
    def _validate_field(field_type: str, options: list[str]) -> None:
        if field_type not in ALLOWED_TYPES:
            raise ValidationException("Nieobsługiwany typ pola")
        if field_type in CHOICE_TYPES and len(options) < 2:
            raise ValidationException("Pole wyboru wymaga co najmniej dwóch opcji")
        if len(options) != len(set(options)):
            raise ValidationException("Opcje odpowiedzi nie mogą się powtarzać")

    @staticmethod
    def _validate_answers(
        fields: list[RecruitmentField], raw_answers: dict[str, Any]
    ) -> list[dict[str, Any]]:
        if len(json.dumps(raw_answers, ensure_ascii=False)) > 100_000:
            raise ValidationException("Formularz zawiera zbyt dużo danych")

        max_lengths = {
            "full_name": 200,
            "email": 255,
            "phone": 30,
            "social_link": 500,
            "availability": 10_000,
        }
        result = []
        for field in fields:
            value = raw_answers.get(field.key)
            if field.field_type == "checkbox":
                if value is not None and not isinstance(value, bool):
                    raise ValidationException(
                        f"Nieprawidłowa odpowiedź w polu „{field.label}”"
                    )
            elif value is not None and not isinstance(value, str):
                raise ValidationException(f"Pole „{field.label}” musi zawierać tekst")
            if isinstance(value, str):
                value = value.strip()
            empty = value is None or value == "" or value == [] or value is False
            if field.required and empty:
                raise ValidationException(f"Pole „{field.label}” jest wymagane")
            if (
                not empty
                and field.field_type in CHOICE_TYPES
                and value not in field.options
            ):
                raise ValidationException(
                    f"Nieprawidłowa odpowiedź w polu „{field.label}”"
                )
            if (
                not empty
                and field.field_type == "email"
                and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", str(value))
            ):
                raise ValidationException("Podaj prawidłowy adres e-mail")
            max_length = max_lengths.get(
                field.key, 10_000 if field.field_type == "textarea" else 2_000
            )
            if isinstance(value, str) and len(value) > max_length:
                raise ValidationException(
                    f"Odpowiedź w polu „{field.label}” jest zbyt długa"
                )
            if not empty and field.field_type == "date":
                try:
                    date.fromisoformat(str(value))
                except ValueError as error:
                    raise ValidationException(
                        f"Nieprawidłowa data w polu „{field.label}”"
                    ) from error
            result.append(
                {
                    "key": field.key,
                    "label": field.label,
                    "field_type": field.field_type,
                    "value": value,
                }
            )
        return result
