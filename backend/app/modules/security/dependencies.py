from collections.abc import Callable

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.dependencies import get_db
from app.modules.core_data.models import User
from app.modules.core_data.repositories.users import UserRepository
from app.modules.security.models.constants import (
    ALL_PERMISSION_CODES,
    CAN_MANAGE_SECURITY,
)
from app.modules.security.repositories import PermissionRepository
from app.modules.security.services.auth import AuthService
from app.modules.security.services.permissions import PermissionService
from app.modules.security.services.token import TokenService


def get_token_service() -> TokenService:
    settings = get_settings()
    return TokenService(
        secret_key=settings.secret_key,
        algorithm=settings.algorithm,
        access_token_expire_minutes=settings.access_token_expire_minutes,
    )


def get_user_repo(session: Session = Depends(get_db)) -> UserRepository:
    """Get user repository dependency."""
    return UserRepository(session)


def get_permission_repo(
    session: Session = Depends(get_db),
) -> PermissionRepository:
    return PermissionRepository(session)


def get_permission_service(
    repo: PermissionRepository = Depends(get_permission_repo),
    users: UserRepository = Depends(get_user_repo),
) -> PermissionService:
    return PermissionService(repo, users)


def get_auth_service(
    repo: UserRepository = Depends(get_user_repo),
    token_service: TokenService = Depends(get_token_service),
    permissions: PermissionService = Depends(get_permission_service),
) -> AuthService:
    return AuthService(repo, token_service, permissions)


def get_current_user(
    authorization: str = Header(None),
    repo: UserRepository = Depends(get_user_repo),
    token_service: TokenService = Depends(get_token_service),
) -> User:
    """Get current authenticated user from Authorization header."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization.split(" ", 1)[1]
    payload = token_service.decode_token(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None

    user = repo.get_by_id(user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def require_permission(permission_code: str) -> Callable[..., User]:
    """Require a permission inherited from any user security group."""

    def dependency(
        user: User = Depends(get_current_user),
        permissions: PermissionService = Depends(get_permission_service),
    ) -> User:
        if not permissions.has_permission(user, permission_code):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return user

    return dependency


def require_any_permission(*permission_codes: str) -> Callable[..., User]:
    """Require at least one of the supplied permissions."""

    def dependency(
        user: User = Depends(get_current_user),
        permissions: PermissionService = Depends(get_permission_service),
    ) -> User:
        effective = permissions.permissions_for_user(user)
        if not effective.intersection(permission_codes):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return user

    return dependency


# Backward-compatible aliases for code that has not yet moved to an
# action-specific permission. They are group-based and never inspect User.status.
require_admin = require_permission(CAN_MANAGE_SECURITY)
require_staff = require_any_permission(*ALL_PERMISSION_CODES)
