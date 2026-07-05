"""Admin users API endpoints."""

from fastapi import APIRouter, Depends, Query

from app.core.audit import AuditReaderPort, EntityType
from app.modules.audit.dependencies import get_audit_reader
from app.modules.audit.schemas import AuditEventResponse
from app.modules.core_data.dependencies import get_user_service
from app.modules.core_data.models import User
from app.modules.core_data.schemas.users import (
    UserCreateRequest,
    UserResponse,
    UserUpdateRequest,
)
from app.modules.core_data.services.users import UserService
from app.modules.security.dependencies import require_any_permission, require_permission
from app.modules.security.models.constants import (
    CAN_MANAGE_USERS,
    CAN_VIEW_SECURITY,
    CAN_VIEW_USERS,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserResponse])
def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: str | None = Query(None),
    status: str | None = Query(None),
    is_active: bool | None = Query(None),
    service: UserService = Depends(get_user_service),
    _user: User = Depends(require_any_permission(CAN_VIEW_USERS, CAN_VIEW_SECURITY)),
):
    """List users with optional filters."""
    users, _ = service.list_users(
        skip=skip,
        limit=limit,
        search=search,
        status=status,
        is_active=is_active,
    )
    return users


@router.post("", response_model=UserResponse)
def create_user(
    request: UserCreateRequest,
    service: UserService = Depends(get_user_service),
    user: User = Depends(require_permission(CAN_MANAGE_USERS)),
):
    """Create new user."""
    return service.create_user(actor=user, **request.model_dump())


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    service: UserService = Depends(get_user_service),
    _user: User = Depends(require_any_permission(CAN_VIEW_USERS, CAN_VIEW_SECURITY)),
):
    """Get user by ID."""
    return service.get_user_by_id(user_id)


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    request: UserUpdateRequest,
    service: UserService = Depends(get_user_service),
    user: User = Depends(require_permission(CAN_MANAGE_USERS)),
):
    """Update user."""
    return service.update_user(
        user_id, actor=user, **request.model_dump(exclude_unset=True)
    )


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    service: UserService = Depends(get_user_service),
    admin: User = Depends(require_permission(CAN_MANAGE_USERS)),
):
    """Delete user."""
    service.delete_user(user_id, actor=admin)
    return {"message": "User deleted successfully"}


@router.get("/{user_id}/audit", response_model=list[AuditEventResponse])
def user_audit_history(
    user_id: int,
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
    service: UserService = Depends(get_user_service),
    audit: AuditReaderPort = Depends(get_audit_reader),
    _user: User = Depends(require_any_permission(CAN_VIEW_USERS, CAN_VIEW_SECURITY)),
):
    service.get_user_by_id(user_id)
    return audit.get_logs_for_entity(
        EntityType.CORE_DATA_USER.value,
        str(user_id),
        limit=limit,
        offset=offset,
    )
