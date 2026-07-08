"""Groups API endpoints for PI domain."""

from fastapi import APIRouter, Depends, Query

from app.core.audit import AuditReaderPort, EntityType
from app.modules.audit.dependencies import get_audit_reader
from app.modules.audit.schemas import AuditEventResponse
from app.modules.core_data.models import User
from app.modules.pi.dependencies import get_assignment_service, get_group_service
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
from app.modules.security.models.constants import (
    CAN_MANAGE_PI_GROUPS,
    CAN_VIEW_PI_GROUPS,
)

router = APIRouter(tags=["groups"])


# =========================================================
# Group endpoints
# =========================================================


@router.get("/groups", response_model=list[GroupResponse])
def list_groups(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    name: str | None = Query(None),
    service: GroupService = Depends(get_group_service),
    _user: User = Depends(require_permission(CAN_VIEW_PI_GROUPS)),
):
    """List all groups with optional filters."""
    groups, _ = service.list_groups(skip=skip, limit=limit, name=name)
    return groups or []


@router.post("/groups", response_model=GroupDetailResponse)
def create_group(
    request: GroupCreateRequest,
    service: GroupService = Depends(get_group_service),
    user: User = Depends(require_permission(CAN_MANAGE_PI_GROUPS)),
):
    """Create new group."""
    return service.create_group(actor=user, **request.model_dump(by_alias=False))


@router.get("/groups/{group_id}", response_model=GroupDetailResponse)
def get_group(
    group_id: int,
    service: GroupService = Depends(get_group_service),
    _user: User = Depends(require_permission(CAN_VIEW_PI_GROUPS)),
):
    """Get group by ID with beneficiaries and volunteers."""
    return service.get_group_detail(group_id)


@router.patch("/groups/{group_id}", response_model=GroupDetailResponse)
def update_group(
    group_id: int,
    request: GroupUpdateRequest,
    service: GroupService = Depends(get_group_service),
    user: User = Depends(require_permission(CAN_MANAGE_PI_GROUPS)),
):
    """Update group."""
    update_data = request.model_dump(exclude_unset=True, by_alias=False)
    return service.update_group(group_id, actor=user, **update_data)


@router.delete("/groups/{group_id}")
def delete_group(
    group_id: int,
    service: GroupService = Depends(get_group_service),
    user: User = Depends(require_permission(CAN_MANAGE_PI_GROUPS)),
):
    """Delete group."""
    service.delete_group(group_id, actor=user)
    return {"message": "Group deleted successfully"}


@router.get("/groups/{group_id}/audit", response_model=list[AuditEventResponse])
def group_audit_history(
    group_id: int,
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
    service: GroupService = Depends(get_group_service),
    audit: AuditReaderPort = Depends(get_audit_reader),
    _user: User = Depends(require_permission(CAN_VIEW_PI_GROUPS)),
):
    service.get_group_by_id(group_id)
    return audit.get_logs_for_entity_or_context(
        EntityType.PI_GROUP.value,
        str(group_id),
        limit=limit,
        offset=offset,
    )


# =========================================================
# Assignment endpoints
# =========================================================


@router.get("/assignments", response_model=list[BeneficiaryAssignmentResponse])
def list_assignments(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: BeneficiaryAssignmentService = Depends(get_assignment_service),
    _user: User = Depends(require_permission(CAN_VIEW_PI_GROUPS)),
):
    """List all beneficiary assignments."""
    assignments = service.list_assignments(skip=skip, limit=limit)
    return assignments or []


@router.post("/assignments", response_model=BeneficiaryAssignmentResponse)
def create_assignment(
    request: BeneficiaryAssignmentCreateRequest,
    service: BeneficiaryAssignmentService = Depends(get_assignment_service),
    user: User = Depends(require_permission(CAN_MANAGE_PI_GROUPS)),
):
    """Create new beneficiary assignment."""
    return service.create_assignment(
        beneficiary_id=request.beneficiary_id,
        volunteer_id=request.volunteer_id,
        actor=user,
        is_main=request.is_main,
        additional_info=request.additional_info,
    )


@router.get(
    "/assignments/{assignment_id}", response_model=BeneficiaryAssignmentResponse
)
def get_assignment(
    assignment_id: int,
    service: BeneficiaryAssignmentService = Depends(get_assignment_service),
    _user: User = Depends(require_permission(CAN_VIEW_PI_GROUPS)),
):
    """Get assignment by ID."""
    return service.get_assignment_by_id(assignment_id)


@router.patch(
    "/assignments/{assignment_id}", response_model=BeneficiaryAssignmentResponse
)
def update_assignment(
    assignment_id: int,
    request: BeneficiaryAssignmentUpdateRequest,
    service: BeneficiaryAssignmentService = Depends(get_assignment_service),
    user: User = Depends(require_permission(CAN_MANAGE_PI_GROUPS)),
):
    """Update assignment."""
    update_data = request.model_dump(exclude_unset=True)
    return service.update_assignment(assignment_id, actor=user, **update_data)


@router.delete("/assignments/{assignment_id}")
def delete_assignment(
    assignment_id: int,
    service: BeneficiaryAssignmentService = Depends(get_assignment_service),
    user: User = Depends(require_permission(CAN_MANAGE_PI_GROUPS)),
):
    """Delete assignment."""
    service.delete_assignment(assignment_id, actor=user)
    return {"message": "Assignment deleted successfully"}
