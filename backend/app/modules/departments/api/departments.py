"""Departments API endpoints."""

from fastapi import APIRouter, Depends, Query

from app.modules.core_data.models import User
from app.modules.departments.dependencies import get_department_service
from app.modules.departments.schemas.departments import (
    DepartmentCreateRequest,
    DepartmentDetailResponse,
    DepartmentListItem,
    DepartmentUpdateRequest,
    MemberAddRequest,
)
from app.modules.departments.services.departments import DepartmentService
from app.modules.security.dependencies import require_permission
from app.modules.security.models.constants import (
    CAN_MANAGE_DEPARTMENTS,
    CAN_VIEW_DEPARTMENTS,
)

router = APIRouter(prefix="/departments", tags=["departments"])


@router.get("", response_model=list[DepartmentListItem])
def list_departments(
    include_archived: bool = Query(False),
    service: DepartmentService = Depends(get_department_service),
    _user: User = Depends(require_permission(CAN_VIEW_DEPARTMENTS)),
):
    """List departments with member counts."""
    return service.list_departments(include_archived=include_archived)


@router.post("", response_model=DepartmentDetailResponse)
def create_department(
    request: DepartmentCreateRequest,
    service: DepartmentService = Depends(get_department_service),
    _user: User = Depends(require_permission(CAN_MANAGE_DEPARTMENTS)),
):
    """Create a new department."""
    return service.create_department(**request.model_dump())


@router.get("/{department_id}", response_model=DepartmentDetailResponse)
def get_department(
    department_id: int,
    service: DepartmentService = Depends(get_department_service),
    _user: User = Depends(require_permission(CAN_VIEW_DEPARTMENTS)),
):
    """Get department detail with members."""
    return service.get_department_detail(department_id)


@router.patch("/{department_id}", response_model=DepartmentDetailResponse)
def update_department(
    department_id: int,
    request: DepartmentUpdateRequest,
    service: DepartmentService = Depends(get_department_service),
    _user: User = Depends(require_permission(CAN_MANAGE_DEPARTMENTS)),
):
    """Update a department; set is_archived to archive/restore (no hard delete)."""
    update_data = request.model_dump(exclude_unset=True)
    return service.update_department(department_id, **update_data)


@router.post("/{department_id}/members", response_model=DepartmentDetailResponse)
def add_member(
    department_id: int,
    request: MemberAddRequest,
    service: DepartmentService = Depends(get_department_service),
    _user: User = Depends(require_permission(CAN_MANAGE_DEPARTMENTS)),
):
    """Add a volunteer to the department."""
    return service.add_member(department_id, request.volunteer_id)


@router.delete(
    "/{department_id}/members/{volunteer_id}",
    response_model=DepartmentDetailResponse,
)
def remove_member(
    department_id: int,
    volunteer_id: int,
    service: DepartmentService = Depends(get_department_service),
    _user: User = Depends(require_permission(CAN_MANAGE_DEPARTMENTS)),
):
    """Remove a volunteer from the department."""
    return service.remove_member(department_id, volunteer_id)
