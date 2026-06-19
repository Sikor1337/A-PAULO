"""Roles API endpoints."""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.modules.core_data.schemas.roles import (
    RoleCreateRequest,
    RoleUpdateRequest,
    RoleResponse,
)
from app.modules.core_data.services.roles import RoleService

router = APIRouter(prefix="/roles", tags=["roles"])


@router.get("", response_model=list[RoleResponse])
def list_roles(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    name: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    session: Session = Depends(get_db),
):
    """List all roles with optional filters."""
    service = RoleService(session)
    roles, _ = service.list_roles(skip=skip, limit=limit, name=name, is_active=is_active)
    return roles


@router.post("", response_model=RoleResponse)
def create_role(
    request: RoleCreateRequest,
    session: Session = Depends(get_db),
):
    """Create new role."""
    service = RoleService(session)
    role = service.create_role(**request.model_dump())
    return role


@router.get("/{role_id}", response_model=RoleResponse)
def get_role(
    role_id: int,
    session: Session = Depends(get_db),
):
    """Get role by ID."""
    service = RoleService(session)
    role = service.get_role_by_id(role_id)
    return role


@router.patch("/{role_id}", response_model=RoleResponse)
def update_role(
    role_id: int,
    request: RoleUpdateRequest,
    session: Session = Depends(get_db),
):
    """Update role."""
    service = RoleService(session)
    update_data = request.model_dump(exclude_unset=True)
    role = service.update_role(role_id, **update_data)
    return role


@router.delete("/{role_id}")
def delete_role(
    role_id: int,
    session: Session = Depends(get_db),
):
    """Delete role."""
    service = RoleService(session)
    service.delete_role(role_id)
    return {"message": "Role deleted successfully"}
