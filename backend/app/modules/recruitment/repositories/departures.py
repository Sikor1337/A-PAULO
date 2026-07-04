"""Data access for volunteer departure interviews."""

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.modules.pi.models.volunteer import Volunteer
from app.modules.recruitment.models import (
    DepartureField,
    DepartureInterview,
    RecruitmentSubmission,
)


class DepartureRepository:
    def __init__(self, session: Session):
        self.session = session

    def list_fields(self, *, active_only: bool = False) -> list[DepartureField]:
        query = self.session.query(DepartureField)
        if active_only:
            query = query.filter(DepartureField.is_active.is_(True))
        return query.order_by(DepartureField.position, DepartureField.id).all()

    def create_field(self, **values) -> DepartureField:
        field = DepartureField(**values)
        self.session.add(field)
        return field

    def delete_field(self, field: DepartureField) -> None:
        self.session.delete(field)

    def get_volunteer(self, volunteer_id: int) -> Volunteer | None:
        return self.session.get(Volunteer, volunteer_id)

    def get_volunteer_for_user(self, user_id: int, email: str) -> Volunteer | None:
        submission = (
            self.session.query(RecruitmentSubmission)
            .filter(RecruitmentSubmission.user_id == user_id)
            .one_or_none()
        )
        if submission and submission.volunteer_id is not None:
            volunteer = self.get_volunteer(submission.volunteer_id)
            if volunteer is not None:
                return volunteer
        matches = (
            self.session.query(Volunteer)
            .filter(func.lower(Volunteer.email) == email.strip().lower())
            .limit(2)
            .all()
        )
        return matches[0] if len(matches) == 1 else None

    def get_by_volunteer(self, volunteer_id: int) -> DepartureInterview | None:
        return (
            self.session.query(DepartureInterview)
            .options(joinedload(DepartureInterview.volunteer))
            .filter(DepartureInterview.volunteer_id == volunteer_id)
            .one_or_none()
        )

    def get(self, interview_id: int) -> DepartureInterview | None:
        return (
            self.session.query(DepartureInterview)
            .options(joinedload(DepartureInterview.volunteer))
            .filter(DepartureInterview.id == interview_id)
            .one_or_none()
        )

    def list(self, *, skip: int = 0, limit: int = 100) -> list[DepartureInterview]:
        return (
            self.session.query(DepartureInterview)
            .options(joinedload(DepartureInterview.volunteer))
            .order_by(DepartureInterview.departure_date.desc(), DepartureInterview.id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create(self, **values) -> DepartureInterview:
        interview = DepartureInterview(**values)
        self.session.add(interview)
        return interview
