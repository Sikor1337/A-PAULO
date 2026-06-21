"""Admin users API endpoints."""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.modules.core_data.models import User
from app.modules.core_data.schemas.users import (
    UserCreateRequest,
    UserResponse,
    UserUpdateRequest,
)
from app.modules.core_data.services.users import UserService
from app.modules.security.dependencies import require_admin

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserResponse])
def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    session: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """List users with optional filters."""
    service = UserService(session)
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
    session: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """Create new user."""
    service = UserService(session)
    return service.create_user(**request.model_dump())


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    session: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """Get user by ID."""
    service = UserService(session)
    return service.get_user_by_id(user_id)


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    request: UserUpdateRequest,
    session: Session = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """Update user."""
    service = UserService(session)
    return service.update_user(user_id, **request.model_dump(exclude_unset=True))


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    session: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """Delete user."""
    service = UserService(session)
    service.delete_user(user_id, current_user_id=admin.id)
    return {"message": "User deleted successfully"}
