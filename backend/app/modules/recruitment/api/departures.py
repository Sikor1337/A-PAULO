"""Staff endpoints for volunteer departure interviews."""

from fastapi import APIRouter, Depends, Query, status

from app.modules.core_data.models import User
from app.modules.recruitment.departure_dependencies import get_departure_service
from app.modules.recruitment.schemas.departures import (
    DepartureFieldResponse,
    DepartureFieldsUpdate,
    DepartureInterviewCreate,
    DepartureInterviewResponse,
)
from app.modules.recruitment.services.departures import DepartureService
from app.modules.security.dependencies import require_staff

router = APIRouter(prefix="/recruitment/departures", tags=["volunteer departures"])


@router.get("/fields", response_model=list[DepartureFieldResponse])
def list_departure_fields(
    service: DepartureService = Depends(get_departure_service),
    _user: User = Depends(require_staff),
):
    return service.list_fields()


@router.put("/fields", response_model=list[DepartureFieldResponse])
def save_departure_fields(
    request: DepartureFieldsUpdate,
    service: DepartureService = Depends(get_departure_service),
    _user: User = Depends(require_staff),
):
    return service.save_fields(request.fields)


@router.get("", response_model=list[DepartureInterviewResponse])
def list_departure_interviews(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    service: DepartureService = Depends(get_departure_service),
    _user: User = Depends(require_staff),
):
    return service.list_interviews(skip=skip, limit=limit)


@router.get("/{interview_id}", response_model=DepartureInterviewResponse)
def get_departure_interview(
    interview_id: int,
    service: DepartureService = Depends(get_departure_service),
    _user: User = Depends(require_staff),
):
    return service.get_interview(interview_id)


@router.post(
    "", response_model=DepartureInterviewResponse, status_code=status.HTTP_201_CREATED
)
def create_departure_interview(
    request: DepartureInterviewCreate,
    service: DepartureService = Depends(get_departure_service),
    user: User = Depends(require_staff),
):
    return service.create_interview(request.volunteer_id, request.answers, user.id)
