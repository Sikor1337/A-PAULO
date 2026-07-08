"""Volunteers API endpoints for PI domain."""

from fastapi import APIRouter, Depends, Query

from app.core.audit import AuditReaderPort, EntityType
from app.modules.audit.dependencies import get_audit_reader
from app.modules.audit.schemas import AuditEventResponse
from app.modules.core_data.models import User
from app.modules.pi.dependencies import get_volunteer_service
from app.modules.pi.schemas.volunteers import (
    VolunteerCreateRequest,
    VolunteerResponse,
    VolunteerUpdateRequest,
)
from app.modules.pi.services.volunteers import VolunteerService
from app.modules.security.dependencies import require_permission
from app.modules.security.models.constants import (
    CAN_MANAGE_VOLUNTEERS,
    CAN_VIEW_VOLUNTEERS,
)

router = APIRouter(prefix="/volunteers", tags=["volunteers"])


@router.get("", response_model=list[VolunteerResponse])
def list_volunteers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    full_name: str | None = Query(None),
    email: str | None = Query(None),
    status: str | None = Query(None),
    service: VolunteerService = Depends(get_volunteer_service),
    _user: User = Depends(require_permission(CAN_VIEW_VOLUNTEERS)),
):
    """List all volunteers with optional filters."""
    volunteers, _ = service.list_volunteers(
        skip=skip,
        limit=limit,
        full_name=full_name,
        email=email,
        status=status,
    )
    return volunteers


@router.post("", response_model=VolunteerResponse)
def create_volunteer(
    request: VolunteerCreateRequest,
    service: VolunteerService = Depends(get_volunteer_service),
    user: User = Depends(require_permission(CAN_MANAGE_VOLUNTEERS)),
):
    """Create new volunteer."""
    return service.create_volunteer(actor=user, **request.model_dump())


@router.get("/{volunteer_id}", response_model=VolunteerResponse)
def get_volunteer(
    volunteer_id: int,
    service: VolunteerService = Depends(get_volunteer_service),
    _user: User = Depends(require_permission(CAN_VIEW_VOLUNTEERS)),
):
    """Get volunteer by ID."""
    return service.get_volunteer_by_id(volunteer_id)


@router.patch("/{volunteer_id}", response_model=VolunteerResponse)
def update_volunteer(
    volunteer_id: int,
    request: VolunteerUpdateRequest,
    service: VolunteerService = Depends(get_volunteer_service),
    user: User = Depends(require_permission(CAN_MANAGE_VOLUNTEERS)),
):
    """Update volunteer."""
    # Only update provided fields
    update_data = request.model_dump(exclude_unset=True)
    return service.update_volunteer(volunteer_id, actor=user, **update_data)


@router.delete("/{volunteer_id}")
def delete_volunteer(
    volunteer_id: int,
    service: VolunteerService = Depends(get_volunteer_service),
    user: User = Depends(require_permission(CAN_MANAGE_VOLUNTEERS)),
):
    """Delete volunteer."""
    service.delete_volunteer(volunteer_id, actor=user)
    return {"message": "Volunteer deleted successfully"}


@router.get("/{volunteer_id}/audit", response_model=list[AuditEventResponse])
def volunteer_audit_history(
    volunteer_id: int,
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
    service: VolunteerService = Depends(get_volunteer_service),
    audit: AuditReaderPort = Depends(get_audit_reader),
    _user: User = Depends(require_permission(CAN_VIEW_VOLUNTEERS)),
):
    service.get_volunteer_by_id(volunteer_id)
    return audit.get_logs_for_entity(
        EntityType.PI_VOLUNTEER.value,
        str(volunteer_id),
        limit=limit,
        offset=offset,
    )
