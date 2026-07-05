"""Business rules for configurable forms and candidate onboarding."""

import re
import unicodedata
from datetime import UTC, datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import ConflictError, NotFoundError, ValidationException
from app.modules.core_data.models import User
from app.modules.recruitment.constants import (
    DEFAULT_FIELDS,
    NEW_VOLUNTEER_STATUS,
    ONBOARDING_MEETING_TYPES,
    SUBMISSION_STATUSES,
)
from app.modules.recruitment.models import (
    RecruitmentField,
    RecruitmentOnboardingMeeting,
    RecruitmentSubmission,
)
from app.modules.recruitment.repositories import RecruitmentRepository
from app.modules.recruitment.schemas import (
    RecruitmentFieldDraft,
    RecruitmentSubmissionCreate,
)
from app.modules.security.models.constants import STAFF_GROUP_KEY
from app.modules.security.services.permissions import PermissionService


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
        current = self.repo.list_fields()
        defaults = (
            DEFAULT_FIELDS
            if not current
            else [values for values in DEFAULT_FIELDS if values["is_system"]]
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
            values["key"] for values in DEFAULT_FIELDS if values["is_system"]
        ]
        ordered = [by_key[key] for key in system_keys]
        if current:
            ordered.extend(field for field in current if field.key not in system_keys)
        else:
            ordered.extend(
                by_key[values["key"]]
                for values in DEFAULT_FIELDS
                if not values["is_system"]
            )
        for position, field in enumerate(ordered):
            if field.position != position:
                field.position = position

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
        try:
            submission = self.get_submission(submission_id)
            if submission.status != "SUBMITTED":
                raise ConflictError("Ta zmiana statusu nie jest dostępna")
            submission.status = "ONBOARDING"
            submission.decision_comment = None
            submission.status_changed_at = datetime.now(UTC)
            self._ensure_onboarding_meetings(submission)
            self.session.commit()
            return self.get_submission(submission.id)
        except Exception:
            self.session.rollback()
            raise

    def set_onboarding_attendance(
        self, submission_id: int, meeting_type: str, attended: bool
    ) -> RecruitmentSubmission:
        if meeting_type not in ONBOARDING_MEETING_TYPES:
            raise ValidationException("Nieznany typ spotkania wdrożeniowego")
        try:
            submission = self.get_submission(submission_id)
            if submission.status != "ONBOARDING":
                raise ConflictError("Obecność można zmieniać tylko podczas wdrażania")
            self._ensure_onboarding_meetings(submission)
            meeting = next(
                item
                for item in submission.onboarding_meetings
                if item.meeting_type == meeting_type
            )
            if attended and meeting.attended_at is None:
                meeting.attended_at = datetime.now(UTC)
            elif not attended:
                meeting.attended_at = None
            self.session.commit()
            return self.get_submission(submission.id)
        except Exception:
            self.session.rollback()
            raise

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
            completed = {
                meeting.meeting_type
                for meeting in submission.onboarding_meetings
                if meeting.attended_at is not None
            }
            if completed != set(ONBOARDING_MEETING_TYPES):
                raise ConflictError(
                    "Promocja wymaga obecności na wszystkich 4 spotkaniach "
                    "wdrożeniowych"
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
                    notes="",
                    history="",
                )
            else:
                volunteer.full_name = submission.full_name
                volunteer.email = submission.email
                volunteer.phone = submission.phone
                volunteer.social_link = submission.social_link or None
                volunteer.status = "Aktywny"
            submission.volunteer_id = volunteer.id
            submission.status = "ACCEPTED"
            submission.decision_comment = comment
            submission.status_changed_at = datetime.now(UTC)
            submission.user.status = "regular"
            PermissionService(self.session).assign_default_group(submission.user)
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
                    submission.volunteer_id = None
                    self.session.flush()
                    self.repo.delete_volunteer(volunteer)
            submission.user.status = NEW_VOLUNTEER_STATUS
            PermissionService(self.session).remove_system_group(
                submission.user, STAFF_GROUP_KEY
            )
            submission.status = "ONBOARDING"
            submission.decision_comment = None
            submission.status_changed_at = datetime.now(UTC)
            self._ensure_onboarding_meetings(submission)
            self.session.commit()
            return self.get_submission(submission.id)
        except Exception:
            self.session.rollback()
            raise

    def _ensure_onboarding_meetings(self, submission: RecruitmentSubmission) -> None:
        existing = {meeting.meeting_type for meeting in submission.onboarding_meetings}
        for meeting_type in ONBOARDING_MEETING_TYPES:
            if meeting_type not in existing:
                submission.onboarding_meetings.append(
                    RecruitmentOnboardingMeeting(meeting_type=meeting_type)
                )
        self.session.flush()

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
