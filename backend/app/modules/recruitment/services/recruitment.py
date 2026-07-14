"""Business rules for configurable forms and candidate onboarding."""

from datetime import UTC, datetime

from sqlalchemy.exc import IntegrityError

from app.core.audit import AuditEntry, AuditPort, EntityType, calculate_delta
from app.core.errors import ConflictError, NotFoundError, ValidationException
from app.modules.core_data.audit_state import user_audit_state
from app.modules.core_data.models import User
from app.modules.pi.audit_state import volunteer_audit_state
from app.modules.recruitment.constants import (
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
from app.modules.recruitment.schemas.commands import (
    RecruitmentSubmissionWrite,
    RecruitmentVolunteerWrite,
)
from app.modules.recruitment.services.form_fields import (
    ConfigurableFormFieldService,
    FieldSaveErrors,
    save_field_drafts,
)
from app.modules.security.models.constants import STAFF_GROUP_KEY
from app.modules.security.services.permissions import PermissionService


class RecruitmentService(
    ConfigurableFormFieldService[RecruitmentField, RecruitmentFieldDraft]
):
    def __init__(
        self,
        repo: RecruitmentRepository,
        permissions: PermissionService,
        audit: AuditPort,
    ):
        self.repo = repo
        self.permissions = permissions
        self.audit = audit
        super().__init__(
            repo,
            system_field_is_valid=lambda field, draft: (
                draft.field_type == field.field_type
                and draft.required
                and draft.is_active
            ),
            errors=FieldSaveErrors(
                unknown_field="Co najmniej jedno pole formularza nie istnieje",
                missing_system_field="Nie można usunąć podstawowego pola formularza",
                invalid_system_field=(
                    "Podstawowe pola kontaktowe muszą pozostać aktywne i wymagane"
                ),
            ),
        )

    def _record_entity(
        self,
        entity_type: EntityType,
        entity_id: int,
        action: str,
        actor: User,
        old_state: dict,
        new_state: dict,
    ) -> None:
        self.audit.record(
            AuditEntry(
                entity_type=entity_type.value,
                entity_id=str(entity_id),
                action=action,
                actor_id=str(actor.id),
                actor_display_name=actor.email,
                changes=calculate_delta(old_state, new_state),
            )
        )

    def list_fields(self, *, active_only: bool = False) -> list[RecruitmentField]:
        return self.repo.list_fields(active_only=active_only)

    def save_fields(
        self, drafts: list[RecruitmentFieldDraft]
    ) -> list[RecruitmentField]:
        """Persist the complete editor draft in one transaction."""
        return save_field_drafts(
            self.repo,
            drafts,
            system_field_is_valid=lambda field, draft: (
                draft.field_type == field.field_type
                and draft.required
                and draft.is_active
            ),
            errors=FieldSaveErrors(
                unknown_field="Co najmniej jedno pole formularza nie istnieje",
                missing_system_field="Nie można usunąć podstawowego pola formularza",
                invalid_system_field=(
                    "Podstawowe pola kontaktowe muszą pozostać aktywne i wymagane"
                ),
            ),
        )

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
            command = RecruitmentSubmissionWrite(
                user_id=user.id,
                full_name=str(indexed["full_name"]).strip(),
                email=email,
                phone=str(indexed["phone"]).strip(),
                social_link=str(indexed.get("social_link") or "").strip(),
                availability=str(indexed.get("availability") or "").strip(),
                answers=answers,
                status="SUBMITTED",
                return_reason=None,
                decision_comment=None,
                submitted_at=now,
                status_changed_at=now,
            )
            if existing:
                submission = self.repo.update_submission(existing, command)
            else:
                submission = self.repo.create_submission(command)
            self.repo.commit(skip_audit=True)
            self.repo.refresh(submission)
            return submission
        except IntegrityError as error:
            self.repo.rollback()
            raise ConflictError(
                "Formularz dla tego konta lub adresu e-mail został już wysłany"
            ) from error
        except Exception:
            self.repo.rollback()
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
            self.repo.commit(skip_audit=True)
            return self.get_submission(submission.id)
        except Exception:
            self.repo.rollback()
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
            self.repo.commit(skip_audit=True)
            return self.get_submission(submission.id)
        except Exception:
            self.repo.rollback()
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
            self.repo.commit(skip_audit=True)
            self.repo.refresh(submission)
            return submission
        except Exception:
            self.repo.rollback()
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
        self, submission_id: int, actor: User, comment: str | None = None
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
            old_volunteer_state = volunteer_audit_state(volunteer) if volunteer else {}
            old_user_state = user_audit_state(
                submission.user,
                self.permissions.group_ids_for_user(submission.user.id),
            )
            email_owner = self.repo.get_volunteer_by_email(submission.email)
            if email_owner and (volunteer is None or email_owner.id != volunteer.id):
                raise ConflictError("Wolontariusz z tym adresem e-mail już istnieje")

            if volunteer is None:
                volunteer = self.repo.create_volunteer(
                    RecruitmentVolunteerWrite(
                        full_name=submission.full_name,
                        email=submission.email,
                        phone=submission.phone,
                        social_link=submission.social_link or None,
                        status="Aktywny",
                        join_date=datetime.now(UTC),
                        notes="",
                        history="",
                    )
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
            self.permissions.assign_default_group(submission.user, actor=actor)
            self.repo.flush()
            self._record_entity(
                EntityType.PI_VOLUNTEER,
                volunteer.id,
                "CREATE" if not old_volunteer_state else "UPDATE",
                actor,
                old_volunteer_state,
                volunteer_audit_state(volunteer),
            )
            self._record_entity(
                EntityType.CORE_DATA_USER,
                submission.user.id,
                "RECRUITMENT_ACCEPTED",
                actor,
                old_user_state,
                user_audit_state(
                    submission.user,
                    self.permissions.group_ids_for_user(submission.user.id),
                ),
            )
            self.repo.commit()
            self.repo.refresh(submission)
            return submission
        except Exception:
            self.repo.rollback()
            raise

    def restore_to_onboarding(
        self, submission_id: int, actor: User
    ) -> RecruitmentSubmission:
        try:
            submission = self.get_submission(submission_id)
            if submission.status not in {"ACCEPTED", "REJECTED"}:
                raise ConflictError(
                    "Do wdrażania można cofnąć tylko wdrożoną lub odrzuconą osobę"
                )
            old_user_state = user_audit_state(
                submission.user,
                self.permissions.group_ids_for_user(submission.user.id),
            )
            deleted_volunteer = None
            old_volunteer_state = None
            if submission.volunteer_id is not None:
                volunteer = self.repo.get_volunteer(submission.volunteer_id)
                if volunteer:
                    deleted_volunteer = volunteer
                    old_volunteer_state = volunteer_audit_state(volunteer)
                    submission.volunteer_id = None
                    self.repo.flush()
                    self.repo.delete_volunteer(volunteer)
            submission.user.status = NEW_VOLUNTEER_STATUS
            self.permissions.remove_system_group(
                submission.user, STAFF_GROUP_KEY, actor=actor
            )
            submission.status = "ONBOARDING"
            submission.decision_comment = None
            submission.status_changed_at = datetime.now(UTC)
            self._ensure_onboarding_meetings(submission)
            self.repo.flush()
            if deleted_volunteer and old_volunteer_state:
                self._record_entity(
                    EntityType.PI_VOLUNTEER,
                    deleted_volunteer.id,
                    "DELETE",
                    actor,
                    old_volunteer_state,
                    {},
                )
            self._record_entity(
                EntityType.CORE_DATA_USER,
                submission.user.id,
                "RECRUITMENT_RESTORED",
                actor,
                old_user_state,
                user_audit_state(
                    submission.user,
                    self.permissions.group_ids_for_user(submission.user.id),
                ),
            )
            self.repo.commit()
            return self.get_submission(submission.id)
        except Exception:
            self.repo.rollback()
            raise

    def _ensure_onboarding_meetings(self, submission: RecruitmentSubmission) -> None:
        existing = {meeting.meeting_type for meeting in submission.onboarding_meetings}
        for meeting_type in ONBOARDING_MEETING_TYPES:
            if meeting_type not in existing:
                submission.onboarding_meetings.append(
                    RecruitmentOnboardingMeeting(meeting_type=meeting_type)
                )
        self.repo.flush()

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
            self.repo.commit(skip_audit=True)
            self.repo.refresh(submission)
            return submission
        except Exception:
            self.repo.rollback()
            raise
