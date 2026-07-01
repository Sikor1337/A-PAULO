"""Dependency wiring for the calendar module."""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.modules.calendar.services import (
    CalendarEventService,
    CalendarSubscriptionService,
)


def get_calendar_event_service(
    session: Session = Depends(get_db),
) -> CalendarEventService:
    return CalendarEventService(session)


def get_calendar_subscription_service(
    session: Session = Depends(get_db),
) -> CalendarSubscriptionService:
    return CalendarSubscriptionService(session)
