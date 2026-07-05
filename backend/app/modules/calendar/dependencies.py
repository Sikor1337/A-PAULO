"""Dependency wiring for the calendar module."""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.modules.calendar.repositories import (
    CalendarAuditRepository,
    CalendarEventRepository,
    CalendarFeedTokenRepository,
)
from app.modules.calendar.services import (
    CalendarEventService,
    CalendarSubscriptionService,
)
from app.modules.security.dependencies import get_permission_service
from app.modules.security.services.permissions import PermissionService


def get_event_repository(session: Session = Depends(get_db)) -> CalendarEventRepository:
    return CalendarEventRepository(session)


def get_audit_repository(session: Session = Depends(get_db)) -> CalendarAuditRepository:
    return CalendarAuditRepository(session)


def get_feed_token_repository(
    session: Session = Depends(get_db),
) -> CalendarFeedTokenRepository:
    return CalendarFeedTokenRepository(session)


def get_calendar_event_service(
    events: CalendarEventRepository = Depends(get_event_repository),
    audit: CalendarAuditRepository = Depends(get_audit_repository),
    permissions: PermissionService = Depends(get_permission_service),
) -> CalendarEventService:
    return CalendarEventService(events, audit, permissions)


def get_calendar_subscription_service(
    tokens: CalendarFeedTokenRepository = Depends(get_feed_token_repository),
    events: CalendarEventRepository = Depends(get_event_repository),
    audit: CalendarAuditRepository = Depends(get_audit_repository),
    permissions: PermissionService = Depends(get_permission_service),
) -> CalendarSubscriptionService:
    return CalendarSubscriptionService(tokens, events, audit, permissions)
