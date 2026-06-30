"""Volunteers API endpoints for PI domain."""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.modules.core_data.models import User
from app.modules.pi.schemas.volunteers import (
    VolunteerCreateRequest,
    VolunteerUpdateRequest,
    VolunteerResponse,
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
    full_name: Optional[str] = Query(None),
    email: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    session: Session = Depends(get_db),
    _user: User = Depends(require_permission(CAN_VIEW_VOLUNTEERS)),
):
    """List all volunteers with optional filters."""
    service = VolunteerService(session)
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
    session: Session = Depends(get_db),
    _user: User = Depends(require_permission(CAN_MANAGE_VOLUNTEERS)),
):
    """Create new volunteer."""
    service = VolunteerService(session)
    volunteer = service.create_volunteer(**request.model_dump())
    return volunteer


@router.get("/{volunteer_id}", response_model=VolunteerResponse)
def get_volunteer(
    volunteer_id: int,
    session: Session = Depends(get_db),
    _user: User = Depends(require_permission(CAN_VIEW_VOLUNTEERS)),
):
    """Get volunteer by ID."""
    service = VolunteerService(session)
    volunteer = service.get_volunteer_by_id(volunteer_id)
    return volunteer


@router.patch("/{volunteer_id}", response_model=VolunteerResponse)
def update_volunteer(
    volunteer_id: int,
    request: VolunteerUpdateRequest,
    session: Session = Depends(get_db),
    _user: User = Depends(require_permission(CAN_MANAGE_VOLUNTEERS)),
):
    """Update volunteer."""
    service = VolunteerService(session)
    # Only update provided fields
    update_data = request.model_dump(exclude_unset=True)
    volunteer = service.update_volunteer(volunteer_id, **update_data)
    return volunteer


@router.delete("/{volunteer_id}")
def delete_volunteer(
    volunteer_id: int,
    session: Session = Depends(get_db),
    _user: User = Depends(require_permission(CAN_MANAGE_VOLUNTEERS)),
):
    """Delete volunteer."""
    service = VolunteerService(session)
    service.delete_volunteer(volunteer_id)
    return {"message": "Volunteer deleted successfully"}
