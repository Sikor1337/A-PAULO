from collections.abc import Callable

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.dependencies import get_db
from app.modules.core_data.models import User
from app.modules.core_data.repositories.users import UserRepository
from app.modules.security.services.auth import AuthService
from app.modules.security.models.constants import (
    ALL_PERMISSION_CODES,
    CAN_MANAGE_SECURITY,
)
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


def get_auth_service(
    session: Session = Depends(get_db),
    token_service: TokenService = Depends(get_token_service),
) -> AuthService:
    repo = UserRepository(session)
    return AuthService(repo, token_service, session)


def get_current_user(
    authorization: str = Header(None),
    session: Session = Depends(get_db),
) -> User:
    """Get current authenticated user from Authorization header."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = authorization.split(" ", 1)[1]
    repo = UserRepository(session)
    token_service = TokenService(
        secret_key=get_settings().secret_key,
        algorithm=get_settings().algorithm,
        access_token_expire_minutes=get_settings().access_token_expire_minutes,
    )

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


def require_status(*allowed_statuses: str) -> Callable[[User], User]:
    """Build a FastAPI dependency that allows only selected user statuses."""

    def dependency(user: User = Depends(get_current_user)) -> User:
        if user.status not in allowed_statuses:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return user

    return dependency


require_admin = require_status("admin")
require_staff = require_status("regular", "admin")


def require_permission(permission_code: str) -> Callable[[User, Session], User]:
    """Require a permission inherited from any user security group."""

    def dependency(
        user: User = Depends(get_current_user),
        session: Session = Depends(get_db),
    ) -> User:
        if not PermissionService(session).has_permission(user, permission_code):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return user

    return dependency


def require_any_permission(*permission_codes: str) -> Callable[[User, Session], User]:
    """Require at least one of the supplied permissions."""

    def dependency(
        user: User = Depends(get_current_user),
        session: Session = Depends(get_db),
    ) -> User:
        effective = PermissionService(session).permissions_for_user(user)
        if not effective.intersection(permission_codes):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return user

    return dependency


# Backward-compatible aliases used by existing routers while they migrate to
# action-specific permission checks.
require_admin = require_permission(CAN_MANAGE_SECURITY)
require_staff = require_any_permission(*ALL_PERMISSION_CODES)

