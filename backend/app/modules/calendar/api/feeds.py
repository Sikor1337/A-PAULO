"""Private subscription token lifecycle and public iCalendar feed."""

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from app.core.config import get_settings
from app.modules.calendar.dependencies import get_calendar_subscription_service
from app.modules.calendar.schemas import (
    FeedTokenCreatedResponse,
    FeedTokenStatusResponse,
)
from app.modules.calendar.services import (
    CalendarSubscriptionService,
    serialize_calendar,
)
from app.modules.core_data.models import User
from app.modules.security.dependencies import require_permission
from app.modules.security.models.constants import CAN_VIEW_EVENTS

router = APIRouter(tags=["calendar"])

WARNING = (
    "Każdy posiadacz tego adresu może odczytać opublikowane wydarzenia. "
    "Subskrypcja jest tylko do odczytu, a Google może odświeżać ją z opóźnieniem."
)


@router.get("/calendar/feed-token", response_model=FeedTokenStatusResponse)
def get_feed_token_status(
    user: User = Depends(require_permission(CAN_VIEW_EVENTS)),
    service: CalendarSubscriptionService = Depends(get_calendar_subscription_service),
):
    token = service.status(user)
    return FeedTokenStatusResponse(
        has_active_token=token is not None,
        created_at=token.created_at if token else None,
    )


@router.post(
    "/calendar/feed-token",
    response_model=FeedTokenCreatedResponse,
    status_code=status.HTTP_201_CREATED,
)
def generate_feed_token(
    request: Request,
    user: User = Depends(require_permission(CAN_VIEW_EVENTS)),
    service: CalendarSubscriptionService = Depends(get_calendar_subscription_service),
):
    plain_token, record = service.generate(user)
    feed_url = request.url_for("calendar_feed", token=plain_token)
    if get_settings().environment.lower() == "production":
        feed_url = feed_url.replace(scheme="https")
    return FeedTokenCreatedResponse(
        feed_url=str(feed_url),
        created_at=record.created_at,
        warning=WARNING,
    )


@router.delete("/calendar/feed-token", status_code=status.HTTP_204_NO_CONTENT)
def revoke_feed_token(
    user: User = Depends(require_permission(CAN_VIEW_EVENTS)),
    service: CalendarSubscriptionService = Depends(get_calendar_subscription_service),
):
    service.revoke(user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/calendar-feeds/{token}.ics")
def calendar_feed(
    token: str,
    request: Request,
    service: CalendarSubscriptionService = Depends(get_calendar_subscription_service),
):
    if (
        get_settings().environment.lower() == "production"
        and request.url.scheme != "https"
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    events = service.events_for_token(token)
    return Response(
        serialize_calendar(events),
        media_type="text/calendar; charset=utf-8",
        headers={
            "Cache-Control": "private, no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )
