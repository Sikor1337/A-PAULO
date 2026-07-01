"""Authenticated calendar event endpoints."""

from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, Query, Response, status

from app.modules.calendar.dependencies import get_calendar_event_service
from app.modules.calendar.schemas import (
    EventCreateRequest,
    EventResponse,
    EventUpdateRequest,
)
from app.modules.calendar.services import CalendarEventService, serialize_calendar
from app.modules.core_data.models import User
from app.modules.security.dependencies import require_permission
from app.modules.security.models.constants import CAN_MANAGE_EVENTS, CAN_VIEW_EVENTS

router = APIRouter(prefix="/calendar/events", tags=["calendar"])


@router.get("", response_model=list[EventResponse])
def list_events(
    starts_from: datetime | None = Query(default=None),
    starts_to: datetime | None = Query(default=None),
    event_status: Literal["draft", "published", "cancelled"] | None = Query(
        default=None, alias="status"
    ),
    visibility: Literal["organization", "admins"] | None = Query(default=None),
    sort: Literal["asc", "desc"] = Query(default="asc"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    user: User = Depends(require_permission(CAN_VIEW_EVENTS)),
    service: CalendarEventService = Depends(get_calendar_event_service),
):
    return service.list_events(
        user,
        starts_from=starts_from,
        starts_to=starts_to,
        status=event_status,
        visibility=visibility,
        sort=sort,
        skip=skip,
        limit=limit,
    )


@router.get("/{event_id}.ics")
def download_event(
    event_id: int,
    user: User = Depends(require_permission(CAN_VIEW_EVENTS)),
    service: CalendarEventService = Depends(get_calendar_event_service),
):
    event = service.get_event(event_id, user)
    return Response(
        serialize_calendar([event], name=event.title),
        media_type="text/calendar; charset=utf-8",
        headers={
            "Cache-Control": "private, no-store",
            "Content-Disposition": f'attachment; filename="event-{event.id}.ics"',
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.get("/{event_id}", response_model=EventResponse)
def get_event(
    event_id: int,
    user: User = Depends(require_permission(CAN_VIEW_EVENTS)),
    service: CalendarEventService = Depends(get_calendar_event_service),
):
    return service.get_event(event_id, user)


@router.post("", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
def create_event(
    request: EventCreateRequest,
    user: User = Depends(require_permission(CAN_MANAGE_EVENTS)),
    service: CalendarEventService = Depends(get_calendar_event_service),
):
    return service.create_event(request, user)


@router.patch("/{event_id}", response_model=EventResponse)
def update_event(
    event_id: int,
    request: EventUpdateRequest,
    user: User = Depends(require_permission(CAN_MANAGE_EVENTS)),
    service: CalendarEventService = Depends(get_calendar_event_service),
):
    return service.update_event(event_id, request, user)


@router.post("/{event_id}/cancel", response_model=EventResponse)
def cancel_event(
    event_id: int,
    user: User = Depends(require_permission(CAN_MANAGE_EVENTS)),
    service: CalendarEventService = Depends(get_calendar_event_service),
):
    return service.cancel_event(event_id, user)


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_event(
    event_id: int,
    user: User = Depends(require_permission(CAN_MANAGE_EVENTS)),
    service: CalendarEventService = Depends(get_calendar_event_service),
):
    service.delete_event(event_id, user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
