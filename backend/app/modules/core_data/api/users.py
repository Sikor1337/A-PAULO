"""Admin users API endpoints."""

from fastapi import APIRouter, Depends, Query

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
    _user: User = Depends(require_permission(CAN_MANAGE_USERS)),
):
    """Create new user."""
    return service.create_user(**request.model_dump())


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
    _user: User = Depends(require_permission(CAN_MANAGE_USERS)),
):
    """Update user."""
    return service.update_user(user_id, **request.model_dump(exclude_unset=True))


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    service: UserService = Depends(get_user_service),
    admin: User = Depends(require_permission(CAN_MANAGE_USERS)),
):
    """Delete user."""
    service.delete_user(user_id, current_user_id=admin.id)
    return {"message": "User deleted successfully"}
