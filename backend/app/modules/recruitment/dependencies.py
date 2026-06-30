"""Dependency injection for the recruitment module."""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.modules.recruitment.services import RecruitmentService


def get_recruitment_service(
    session: Session = Depends(get_db),
) -> RecruitmentService:
    return RecruitmentService(session)
