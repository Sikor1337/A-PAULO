"""Groups API endpoints for PI domain."""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.modules.core_data.models import User
from app.modules.pi.schemas.groups import (
    BeneficiaryAssignmentCreateRequest,
    BeneficiaryAssignmentResponse,
    BeneficiaryAssignmentUpdateRequest,
    GroupCreateRequest,
    GroupDetailResponse,
    GroupResponse,
    GroupUpdateRequest,
)
from app.modules.pi.services.groups import BeneficiaryAssignmentService, GroupService
from app.modules.security.dependencies import require_permission
from app.modules.security.models.constants import CAN_MANAGE_PI_GROUPS, CAN_VIEW_PI_GROUPS

router = APIRouter(tags=["groups"])


# =========================================================
# Group endpoints
# =========================================================

@router.get("/groups", response_model=list[GroupResponse])
def list_groups(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    name: Optional[str] = Query(None),
    session: Session = Depends(get_db),
    _user: User = Depends(require_permission(CAN_VIEW_PI_GROUPS)),
):
    """List all groups with optional filters."""
    service = GroupService(session)
    groups, _ = service.list_groups(skip=skip, limit=limit, name=name)
    return groups or []


@router.post("/groups", response_model=GroupDetailResponse)
def create_group(
    request: GroupCreateRequest,
    session: Session = Depends(get_db),
    _user: User = Depends(require_permission(CAN_MANAGE_PI_GROUPS)),
):
    """Create new group."""
    service = GroupService(session)
    group = service.create_group(**request.model_dump(by_alias=False))
    return group


@router.get("/groups/{group_id}", response_model=GroupDetailResponse)
def get_group(
    group_id: int,
    session: Session = Depends(get_db),
    _user: User = Depends(require_permission(CAN_VIEW_PI_GROUPS)),
):
    """Get group by ID with beneficiaries and volunteers."""
    service = GroupService(session)
    return service.get_group_detail(group_id)


@router.patch("/groups/{group_id}", response_model=GroupDetailResponse)
def update_group(
    group_id: int,
    request: GroupUpdateRequest,
    session: Session = Depends(get_db),
    _user: User = Depends(require_permission(CAN_MANAGE_PI_GROUPS)),
):
    """Update group."""
    service = GroupService(session)
    update_data = request.model_dump(exclude_unset=True, by_alias=False)
    group = service.update_group(group_id, **update_data)
    return group


@router.delete("/groups/{group_id}")
def delete_group(
    group_id: int,
    session: Session = Depends(get_db),
    _user: User = Depends(require_permission(CAN_MANAGE_PI_GROUPS)),
):
    """Delete group."""
    service = GroupService(session)
    service.delete_group(group_id)
    return {"message": "Group deleted successfully"}


# =========================================================
# Assignment endpoints
# =========================================================

@router.get("/assignments", response_model=list[BeneficiaryAssignmentResponse])
def list_assignments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    session: Session = Depends(get_db),
    _user: User = Depends(require_permission(CAN_VIEW_PI_GROUPS)),
):
    """List all beneficiary assignments."""
    service = BeneficiaryAssignmentService(session)
    assignments = service.list_assignments(skip=skip, limit=limit)
    return assignments or []


@router.post("/assignments", response_model=BeneficiaryAssignmentResponse)
def create_assignment(
    request: BeneficiaryAssignmentCreateRequest,
    session: Session = Depends(get_db),
    _user: User = Depends(require_permission(CAN_MANAGE_PI_GROUPS)),
):
    """Create new beneficiary assignment."""
    service = BeneficiaryAssignmentService(session)
    assignment = service.create_assignment(
        beneficiary_id=request.beneficiary_id,
        volunteer_id=request.volunteer_id,
        is_main=request.is_main,
        additional_info=request.additional_info,
    )
    return assignment


@router.get("/assignments/{assignment_id}", response_model=BeneficiaryAssignmentResponse)
def get_assignment(
    assignment_id: int,
    session: Session = Depends(get_db),
    _user: User = Depends(require_permission(CAN_VIEW_PI_GROUPS)),
):
    """Get assignment by ID."""
    service = BeneficiaryAssignmentService(session)
    assignment = service.get_assignment_by_id(assignment_id)
    return assignment


@router.patch("/assignments/{assignment_id}", response_model=BeneficiaryAssignmentResponse)
def update_assignment(
    assignment_id: int,
    request: BeneficiaryAssignmentUpdateRequest,
    session: Session = Depends(get_db),
    _user: User = Depends(require_permission(CAN_MANAGE_PI_GROUPS)),
):
    """Update assignment."""
    service = BeneficiaryAssignmentService(session)
    update_data = request.model_dump(exclude_unset=True)
    assignment = service.update_assignment(assignment_id, **update_data)
    return assignment


@router.delete("/assignments/{assignment_id}")
def delete_assignment(
    assignment_id: int,
    session: Session = Depends(get_db),
    _user: User = Depends(require_permission(CAN_MANAGE_PI_GROUPS)),
):
    """Delete assignment."""
    service = BeneficiaryAssignmentService(session)
    service.delete_assignment(assignment_id)
    return {"message": "Assignment deleted successfully"}
