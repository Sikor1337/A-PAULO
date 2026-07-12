"""Persistence for the beneficiary recruitment workflow (PAP-90)."""

from sqlalchemy.orm import Session

from app.infrastructure.sql.repository import SQLRepository
from app.modules.recruitment.models import (
    BeneficiaryRecruitmentField,
    BeneficiaryRecruitmentSubmission,
)


class BeneficiaryRecruitmentRepository(SQLRepository):
    def __init__(self, session: Session):
        self.session = session

    def list_fields(
        self, *, active_only: bool = False
    ) -> list[BeneficiaryRecruitmentField]:
        query = self.session.query(BeneficiaryRecruitmentField)
        if active_only:
            query = query.filter(BeneficiaryRecruitmentField.is_active.is_(True))
        return query.order_by(
            BeneficiaryRecruitmentField.position, BeneficiaryRecruitmentField.id
        ).all()

    def create_field(self, **values) -> BeneficiaryRecruitmentField:
        field = BeneficiaryRecruitmentField(**values)
        self.session.add(field)
        return field

    def delete_field(self, field: BeneficiaryRecruitmentField) -> None:
        self.session.delete(field)

    def list_submissions(
        self,
        *,
        include_archived: bool = False,
        skip: int = 0,
        limit: int = 100,
    ) -> list[BeneficiaryRecruitmentSubmission]:
        query = self.session.query(BeneficiaryRecruitmentSubmission)
        if not include_archived:
            query = query.filter(BeneficiaryRecruitmentSubmission.status != "ARCHIVED")
        return (
            query.order_by(
                BeneficiaryRecruitmentSubmission.submitted_at.desc(),
                BeneficiaryRecruitmentSubmission.id.desc(),
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_submission(
        self, submission_id: int
    ) -> BeneficiaryRecruitmentSubmission | None:
        return self.session.get(BeneficiaryRecruitmentSubmission, submission_id)

    def get_submission_for_update(
        self, submission_id: int
    ) -> BeneficiaryRecruitmentSubmission | None:
        return (
            self.session.query(BeneficiaryRecruitmentSubmission)
            .filter(BeneficiaryRecruitmentSubmission.id == submission_id)
            .with_for_update()
            .first()
        )

    def create_submission(self, **values) -> BeneficiaryRecruitmentSubmission:
        submission = BeneficiaryRecruitmentSubmission(**values)
        self.session.add(submission)
        return submission

    def delete_submission(self, submission: BeneficiaryRecruitmentSubmission) -> None:
        self.session.delete(submission)
