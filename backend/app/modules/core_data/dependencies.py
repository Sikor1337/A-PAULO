"""Dependencies for core_data domain."""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.audit import AuditPort
from app.core.dependencies import get_db
from app.modules.audit.dependencies import get_audit_service
from app.modules.core_data.repositories.users import UserRepository
from app.modules.core_data.services.users import UserService
from app.modules.security.dependencies import get_permission_service
from app.modules.security.services.permissions import PermissionService


def get_user_repo(session: Session = Depends(get_db)) -> UserRepository:
    """Get user repository dependency."""
    return UserRepository(session)


def get_user_service(
    repo: UserRepository = Depends(get_user_repo),
    permissions: PermissionService = Depends(get_permission_service),
    audit: AuditPort = Depends(get_audit_service),
) -> UserService:
    """Get user service dependency."""
    return UserService(repo, permissions, audit)
