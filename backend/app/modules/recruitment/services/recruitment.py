"""Business rules for configurable forms and candidate onboarding."""

import re
import unicodedata
from datetime import UTC, datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import ConflictError, NotFoundError, ValidationException
from app.modules.core_data.models import User
from app.modules.recruitment.models import RecruitmentField, RecruitmentSubmission
from app.modules.recruitment.models.constants import (
    DEFAULT_FIELDS,
    NEW_VOLUNTEER_STATUS,
    SUBMISSION_STATUSES,
)
from app.modules.recruitment.repositories import RecruitmentRepository
from app.modules.recruitment.schemas import (
    RecruitmentFieldDraft,
    RecruitmentSubmissionCreate,
)


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

    def save_fields(
        self, drafts: list[RecruitmentFieldDraft]
    ) -> list[RecruitmentField]:
        """Persist the complete editor draft in one transaction."""

        try:
            current = self.list_fields()
            by_id = {field.id: field for field in current}
            submitted_ids = {draft.id for draft in drafts if draft.id is not None}
            unknown_ids = submitted_ids - set(by_id)
            if unknown_ids:
                raise NotFoundError("Co najmniej jedno pole formularza nie istnieje")

            system_ids = {field.id for field in current if field.is_system}
            if not system_ids.issubset(submitted_ids):
                raise ConflictError("Nie można usunąć podstawowego pola formularza")

            used_keys = {field.key for field in current}
            for position, draft in enumerate(drafts):
                if draft.id is None:
                    base_key = _slugify(draft.label)
                    key = base_key
                    suffix = 2
                    while key in used_keys:
                        key = f"{base_key}_{suffix}"
                        suffix += 1
                    used_keys.add(key)
                    self.repo.create_field(
                        key=key,
                        label=draft.label,
                        field_type=draft.field_type,
                        required=draft.required,
                        placeholder=draft.placeholder,
                        options=draft.options,
                        position=position,
                        is_active=draft.is_active,
                        is_system=False,
                    )
                    continue

                field = by_id[draft.id]
                if field.is_system and (
                    draft.field_type != field.field_type
                    or not draft.required
                    or not draft.is_active
                ):
                    raise ConflictError(
                        "Podstawowe pola kontaktowe muszą pozostać aktywne i wymagane"
                    )
                field.label = draft.label
                field.field_type = draft.field_type
                field.required = draft.required
                field.placeholder = draft.placeholder
                field.options = draft.options
                field.position = position
                field.is_active = draft.is_active

            for field in current:
                if field.id not in submitted_ids:
                    self.repo.delete_field(field)

            self.session.commit()
            return self.repo.list_fields()
        except Exception:
            self.session.rollback()
            raise

    def get_submission_for_user(self, user_id: int) -> RecruitmentSubmission | None:
        return self.repo.get_submission_by_user_id(user_id)

    def submit(
        self, user: User, request: RecruitmentSubmissionCreate
    ) -> RecruitmentSubmission:
        try:
            fields = self.list_fields(active_only=True)
            answers = request.validated_answers(fields)
            indexed = {answer["key"]: answer["value"] for answer in answers}
            email = str(indexed["email"]).strip().lower()
            if email != user.email.lower():
                raise ValidationException(
                    "Adres e-mail w formularzu musi być zgodny z kontem użytkownika"
                )

            existing = self.repo.get_submission_by_user_id(user.id)
            if existing and existing.status != "RETURNED":
                raise ConflictError("Formularz z tego konta został już wysłany")
            email_submission = self.repo.get_submission_by_email(email)
            if email_submission and email_submission is not existing:
                raise ConflictError(
                    "Formularz dla tego adresu e-mail został już wysłany"
                )

            now = datetime.now(UTC)
            values = {
                "user_id": user.id,
                "full_name": str(indexed["full_name"]).strip(),
                "email": email,
                "phone": str(indexed["phone"]).strip(),
                "social_link": str(indexed.get("social_link") or "").strip(),
                "availability": str(indexed.get("availability") or "").strip(),
                "answers": answers,
                "status": "SUBMITTED",
                "return_reason": None,
                "decision_comment": None,
                "submitted_at": now,
                "status_changed_at": now,
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
                "Formularz dla tego konta lub adresu e-mail został już wysłany"
            ) from error
        except Exception:
            self.session.rollback()
            raise

    def list_submissions(self, **filters) -> list[RecruitmentSubmission]:
        status = filters.get("status")
        if status and status not in SUBMISSION_STATUSES:
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
            submission.return_reason = reason
            submission.decision_comment = None
            submission.status_changed_at = datetime.now(UTC)
            self.session.commit()
            self.session.refresh(submission)
            return submission
        except Exception:
            self.session.rollback()
            raise

    def reject(
        self, submission_id: int, comment: str | None = None
    ) -> RecruitmentSubmission:
        return self._transition(
            submission_id,
            {"ONBOARDING"},
            "REJECTED",
            decision_comment=comment,
        )

    def accept(
        self, submission_id: int, comment: str | None = None
    ) -> RecruitmentSubmission:
        try:
            submission = self.get_submission(submission_id)
            if submission.status != "ONBOARDING":
                raise ConflictError(
                    "Tylko osobę we wdrażaniu można oznaczyć jako wdrożoną"
                )
            volunteer = (
                self.repo.get_volunteer(submission.volunteer_id)
                if submission.volunteer_id is not None
                else None
            )
            email_owner = self.repo.get_volunteer_by_email(submission.email)
            if email_owner and (volunteer is None or email_owner.id != volunteer.id):
                raise ConflictError("Wolontariusz z tym adresem e-mail już istnieje")

            if volunteer is None:
                volunteer = self.repo.create_volunteer(
                    full_name=submission.full_name,
                    email=submission.email,
                    phone=submission.phone,
                    social_link=submission.social_link or None,
                    status="Aktywny",
                    join_date=datetime.now(UTC),
                    notes="Utworzono po zakończeniu procesu rekrutacji.",
                    history="Rekrutacja zakończona pomyślnie.",
                )
            else:
                volunteer.full_name = submission.full_name
                volunteer.email = submission.email
                volunteer.phone = submission.phone
                volunteer.social_link = submission.social_link or None
                volunteer.status = "Aktywny"
                volunteer.history = (
                    f"{volunteer.history}\nPonownie zakończono proces rekrutacji."
                ).strip()
            submission.volunteer_id = volunteer.id
            submission.status = "ACCEPTED"
            submission.decision_comment = comment
            submission.status_changed_at = datetime.now(UTC)
            submission.user.status = "regular"
            self.session.commit()
            self.session.refresh(submission)
            return submission
        except Exception:
            self.session.rollback()
            raise

    def restore_to_onboarding(self, submission_id: int) -> RecruitmentSubmission:
        try:
            submission = self.get_submission(submission_id)
            if submission.status not in {"ACCEPTED", "REJECTED"}:
                raise ConflictError(
                    "Do wdrażania można cofnąć tylko wdrożoną lub odrzuconą osobę"
                )
            if submission.volunteer_id is not None:
                volunteer = self.repo.get_volunteer(submission.volunteer_id)
                if volunteer:
                    volunteer.status = "Były"
                    volunteer.history = (
                        f"{volunteer.history}\nCofnięto do etapu wdrażania."
                    ).strip()
            submission.user.status = NEW_VOLUNTEER_STATUS
            submission.status = "ONBOARDING"
            submission.decision_comment = None
            submission.status_changed_at = datetime.now(UTC)
            self.session.commit()
            self.session.refresh(submission)
            return submission
        except Exception:
            self.session.rollback()
            raise

    def _transition(
        self,
        submission_id: int,
        allowed: set[str],
        target: str,
        *,
        decision_comment: str | None = None,
    ) -> RecruitmentSubmission:
        try:
            submission = self.get_submission(submission_id)
            if submission.status not in allowed:
                raise ConflictError(
                    "Ta zmiana statusu nie jest dostępna na obecnym etapie"
                )
            submission.status = target
            submission.decision_comment = decision_comment
            submission.status_changed_at = datetime.now(UTC)
            self.session.commit()
            self.session.refresh(submission)
            return submission
        except Exception:
            self.session.rollback()
            raise
