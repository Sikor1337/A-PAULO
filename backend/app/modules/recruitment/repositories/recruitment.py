"""Data access for recruitment fields and submissions."""

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload, selectinload

from app.infrastructure.sql.repository import SQLRepository
from app.modules.pi.models.volunteer import Volunteer
from app.modules.recruitment.models import RecruitmentField, RecruitmentSubmission
from app.modules.recruitment.schemas.commands import (
    RecruitmentSubmissionWrite,
    RecruitmentVolunteerWrite,
)
from app.modules.recruitment.schemas.form_fields import FormFieldWrite


class RecruitmentRepository(SQLRepository):
    def __init__(self, session: Session):
        self.session = session

    def list_fields(self, *, active_only: bool = False) -> list[RecruitmentField]:
        query = self.session.query(RecruitmentField)
        if active_only:
            query = query.filter(RecruitmentField.is_active.is_(True))
        return query.order_by(RecruitmentField.position, RecruitmentField.id).all()

    def get_field(self, field_id: int) -> RecruitmentField | None:
        return self.session.get(RecruitmentField, field_id)

    def create_field(self, request: FormFieldWrite) -> RecruitmentField:
        field = RecruitmentField(
            key=request.key,
            label=request.label,
            field_type=request.field_type,
            required=request.required,
            placeholder=request.placeholder,
            options=request.options,
            position=request.position,
            is_active=request.is_active,
            is_system=request.is_system,
        )
        self.session.add(field)
        return field

    def delete_field(self, field: RecruitmentField) -> None:
        self.session.delete(field)

    def get_submission(self, submission_id: int) -> RecruitmentSubmission | None:
        return (
            self.session.query(RecruitmentSubmission)
            .options(
                joinedload(RecruitmentSubmission.user),
                selectinload(RecruitmentSubmission.onboarding_meetings),
            )
            .filter(RecruitmentSubmission.id == submission_id)
            .one_or_none()
        )

    def get_submission_by_user_id(self, user_id: int) -> RecruitmentSubmission | None:
        return (
            self.session.query(RecruitmentSubmission)
            .options(
                joinedload(RecruitmentSubmission.user),
                selectinload(RecruitmentSubmission.onboarding_meetings),
            )
            .filter(RecruitmentSubmission.user_id == user_id)
            .one_or_none()
        )

    def get_submission_by_email(self, email: str) -> RecruitmentSubmission | None:
        return (
            self.session.query(RecruitmentSubmission)
            .filter(func.lower(RecruitmentSubmission.email) == email.lower())
            .one_or_none()
        )

    def list_submissions(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        status: str | None = None,
        search: str | None = None,
    ) -> list[RecruitmentSubmission]:
        query = self.session.query(RecruitmentSubmission).options(
            selectinload(RecruitmentSubmission.onboarding_meetings)
        )
        if status:
            query = query.filter(RecruitmentSubmission.status == status)
        if search:
            pattern = f"%{search}%"
            query = query.filter(
                RecruitmentSubmission.full_name.ilike(pattern)
                | RecruitmentSubmission.email.ilike(pattern)
                | RecruitmentSubmission.phone.ilike(pattern)
            )
        return (
            query.order_by(RecruitmentSubmission.submitted_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create_submission(
        self, request: RecruitmentSubmissionWrite
    ) -> RecruitmentSubmission:
        submission = RecruitmentSubmission(
            user_id=request.user_id,
            full_name=request.full_name,
            email=request.email,
            phone=request.phone,
            social_link=request.social_link,
            availability=request.availability,
            answers=request.answers,
            status=request.status,
            return_reason=request.return_reason,
            decision_comment=request.decision_comment,
            submitted_at=request.submitted_at,
            status_changed_at=request.status_changed_at,
        )
        self.session.add(submission)
        return submission

    def update_submission(
        self,
        submission: RecruitmentSubmission,
        request: RecruitmentSubmissionWrite,
    ) -> RecruitmentSubmission:
        submission.user_id = request.user_id
        submission.full_name = request.full_name
        submission.email = request.email
        submission.phone = request.phone
        submission.social_link = request.social_link
        submission.availability = request.availability
        submission.answers = request.answers
        submission.status = request.status
        submission.return_reason = request.return_reason
        submission.decision_comment = request.decision_comment
        submission.submitted_at = request.submitted_at
        submission.status_changed_at = request.status_changed_at
        return submission

    def get_volunteer_by_email(self, email: str) -> Volunteer | None:
        return (
            self.session.query(Volunteer)
            .filter(func.lower(Volunteer.email) == email.lower())
            .one_or_none()
        )

    def get_volunteer(self, volunteer_id: int) -> Volunteer | None:
        return self.session.get(Volunteer, volunteer_id)

    def create_volunteer(self, request: RecruitmentVolunteerWrite) -> Volunteer:
        volunteer = Volunteer(
            full_name=request.full_name,
            email=request.email,
            phone=request.phone,
            social_link=request.social_link,
            status=request.status,
            join_date=request.join_date,
            notes=request.notes,
            history=request.history,
        )
        self.session.add(volunteer)
        self.session.flush()
        return volunteer

    def delete_volunteer(self, volunteer: Volunteer) -> None:
        self.session.delete(volunteer)
