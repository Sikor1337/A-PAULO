"""Internal typed commands passed from recruitment services to repositories."""

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel


class RecruitmentSubmissionWrite(BaseModel):
    user_id: int
    full_name: str
    email: str
    phone: str
    social_link: str
    availability: str
    answers: list[dict[str, Any]]
    status: str
    return_reason: str | None
    decision_comment: str | None
    submitted_at: datetime
    status_changed_at: datetime


class RecruitmentVolunteerWrite(BaseModel):
    full_name: str
    email: str
    phone: str | None
    social_link: str | None
    status: str
    join_date: datetime
    notes: str
    history: str


class DepartureInterviewWrite(BaseModel):
    volunteer_id: int
    departure_date: date
    departure_reason: str
    stay_in_contact: bool
    answers: list[dict[str, Any]]
    completed_by_id: int
