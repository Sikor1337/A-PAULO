"""Endpoints for volunteer departure interviews."""

from fastapi import APIRouter, Depends, Query, status

from app.modules.core_data.models import User
from app.modules.recruitment.departure_dependencies import get_departure_service
from app.modules.recruitment.schemas.departures import (
    DepartureFieldResponse,
    DepartureFieldsUpdate,
    DepartureInterviewCreate,
    DepartureInterviewResponse,
    DepartureSelfServiceResponse,
)
from app.modules.recruitment.services.departures import DepartureService
from app.modules.security.dependencies import require_permission
from app.modules.security.models.constants import (
    CAN_MANAGE_RECRUITMENT,
    CAN_SUBMIT_DEPARTURE_SURVEY,
    CAN_VIEW_RECRUITMENT,
)

router = APIRouter(prefix="/recruitment/departures", tags=["volunteer departures"])


@router.get("/fields", response_model=list[DepartureFieldResponse])
def list_departure_fields(
    service: DepartureService = Depends(get_departure_service),
    _user: User = Depends(require_permission(CAN_VIEW_RECRUITMENT)),
):
    return service.list_fields()


@router.put("/fields", response_model=list[DepartureFieldResponse])
def save_departure_fields(
    request: DepartureFieldsUpdate,
    service: DepartureService = Depends(get_departure_service),
    _user: User = Depends(require_permission(CAN_MANAGE_RECRUITMENT)),
):
    return service.save_fields(request.fields)


@router.get("", response_model=list[DepartureInterviewResponse])
def list_departure_interviews(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    service: DepartureService = Depends(get_departure_service),
    _user: User = Depends(require_permission(CAN_VIEW_RECRUITMENT)),
):
    return service.list_interviews(skip=skip, limit=limit)


@router.get("/me", response_model=DepartureSelfServiceResponse)
def get_my_departure_survey(
    service: DepartureService = Depends(get_departure_service),
    user: User = Depends(require_permission(CAN_SUBMIT_DEPARTURE_SURVEY)),
):
    return service.get_self_service(user)


@router.post(
    "/me",
    response_model=DepartureInterviewResponse,
    status_code=status.HTTP_201_CREATED,
)
def submit_my_departure_survey(
    request: DepartureInterviewCreate,
    service: DepartureService = Depends(get_departure_service),
    user: User = Depends(require_permission(CAN_SUBMIT_DEPARTURE_SURVEY)),
):
    return service.create_self_interview(user, request.answers)


@router.put("/me", response_model=DepartureInterviewResponse)
def update_my_departure_survey(
    request: DepartureInterviewCreate,
    service: DepartureService = Depends(get_departure_service),
    user: User = Depends(require_permission(CAN_SUBMIT_DEPARTURE_SURVEY)),
):
    return service.update_self_interview(user, request.answers)


@router.get("/{interview_id}", response_model=DepartureInterviewResponse)
def get_departure_interview(
    interview_id: int,
    service: DepartureService = Depends(get_departure_service),
    _user: User = Depends(require_permission(CAN_VIEW_RECRUITMENT)),
):
    return service.get_interview(interview_id)
