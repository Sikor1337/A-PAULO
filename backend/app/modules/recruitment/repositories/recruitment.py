"""Data access for recruitment fields and submissions."""

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.modules.recruitment.models import (
    RecruitmentField,
    RecruitmentInvitation,
    RecruitmentSubmission,
)


class RecruitmentRepository:
    def __init__(self, session: Session):
        self.session = session

    def list_fields(self, *, active_only: bool = False) -> list[RecruitmentField]:
        query = self.session.query(RecruitmentField)
        if active_only:
            query = query.filter(RecruitmentField.is_active.is_(True))
        return query.order_by(RecruitmentField.position, RecruitmentField.id).all()

    def get_field(self, field_id: int) -> RecruitmentField | None:
        return self.session.get(RecruitmentField, field_id)

    def create_field(self, **values) -> RecruitmentField:
        field = RecruitmentField(**values)
        self.session.add(field)
        return field

    def delete_field(self, field: RecruitmentField) -> None:
        self.session.delete(field)

    def get_invitation(self, invitation_id: int) -> RecruitmentInvitation | None:
        return self.session.get(RecruitmentInvitation, invitation_id)

    def get_invitation_by_token(self, token: str) -> RecruitmentInvitation | None:
        return (
            self.session.query(RecruitmentInvitation)
            .options(joinedload(RecruitmentInvitation.submission))
            .filter(RecruitmentInvitation.token == token)
            .one_or_none()
        )

    def get_active_invitation_by_email(
        self, email: str
    ) -> RecruitmentInvitation | None:
        return (
            self.session.query(RecruitmentInvitation)
            .filter(
                func.lower(RecruitmentInvitation.recipient_email) == email.lower(),
                RecruitmentInvitation.is_active.is_(True),
            )
            .one_or_none()
        )

    def list_invitations(
        self, *, skip: int = 0, limit: int = 100
    ) -> list[RecruitmentInvitation]:
        return (
            self.session.query(RecruitmentInvitation)
            .options(joinedload(RecruitmentInvitation.submission))
            .order_by(RecruitmentInvitation.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create_invitation(self, **values) -> RecruitmentInvitation:
        invitation = RecruitmentInvitation(**values)
        self.session.add(invitation)
        return invitation

    def get_submission(self, submission_id: int) -> RecruitmentSubmission | None:
        return self.session.get(RecruitmentSubmission, submission_id)

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
        query = self.session.query(RecruitmentSubmission)
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

    def create_submission(self, **values) -> RecruitmentSubmission:
        submission = RecruitmentSubmission(**values)
        self.session.add(submission)
        return submission
