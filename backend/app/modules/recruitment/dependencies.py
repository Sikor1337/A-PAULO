"""Dependency injection and access guards for the recruitment module."""

from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.modules.core_data.models import User
from app.modules.recruitment.access import is_valid_recruitment_access_token
from app.modules.recruitment.constants import (
    NEW_VOLUNTEER_STATUS,
    RECRUITMENT_TOKEN_HEADER,
)
from app.modules.recruitment.repositories import RecruitmentRepository
from app.modules.recruitment.services import RecruitmentService
from app.modules.security.dependencies import get_current_user, get_permission_service
from app.modules.security.services.permissions import PermissionService


def get_recruitment_repository(
    session: Session = Depends(get_db),
) -> RecruitmentRepository:
    return RecruitmentRepository(session)


def get_recruitment_service(
    repo: RecruitmentRepository = Depends(get_recruitment_repository),
    permissions: PermissionService = Depends(get_permission_service),
) -> RecruitmentService:
    return RecruitmentService(repo, permissions)


def require_recruitment_access(
    token: Annotated[str | None, Header(alias=RECRUITMENT_TOKEN_HEADER)] = None,
) -> str:
    if not is_valid_recruitment_access_token(token):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nie znaleziono formularza rekrutacyjnego",
        )
    assert token is not None
    return token


def require_recruitment_candidate(
    user: User = Depends(get_current_user),
) -> User:
    if user.status != NEW_VOLUNTEER_STATUS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Formularz jest dostępny tylko dla zaproszonych kandydatów",
        )
    return user
