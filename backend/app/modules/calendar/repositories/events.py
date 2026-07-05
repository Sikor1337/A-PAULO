"""Persistence operations for calendar events."""

from datetime import datetime

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.infrastructure.sql.repository import SQLRepository
from app.modules.calendar.models import CalendarEvent
from app.modules.calendar.models.constants import DRAFT_STATUS, ORGANIZATION_VISIBILITY


class CalendarEventRepository(SQLRepository):
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, event_id: int) -> CalendarEvent | None:
        return self.session.query(CalendarEvent).filter_by(id=event_id).first()

    def list_visible(
        self,
        *,
        is_admin: bool,
        starts_from: datetime | None = None,
        starts_to: datetime | None = None,
        status: str | None = None,
        visibility: str | None = None,
        sort: str = "asc",
        skip: int = 0,
        limit: int = 100,
    ) -> list[CalendarEvent]:
        query = self.session.query(CalendarEvent)
        if not is_admin:
            query = query.filter(
                CalendarEvent.visibility == ORGANIZATION_VISIBILITY,
                CalendarEvent.status != DRAFT_STATUS,
            )
        if starts_from:
            query = query.filter(
                or_(
                    CalendarEvent.recurrence_rule.is_not(None),
                    CalendarEvent.ends_at >= starts_from,
                )
            )
        if starts_to:
            query = query.filter(CalendarEvent.starts_at <= starts_to)
        if status:
            query = query.filter(CalendarEvent.status == status)
        if visibility:
            query = query.filter(CalendarEvent.visibility == visibility)
        ordering = (
            CalendarEvent.starts_at.desc()
            if sort == "desc"
            else CalendarEvent.starts_at.asc()
        )
        return query.order_by(ordering).offset(skip).limit(limit).all()

    def create(self, **values) -> CalendarEvent:
        event = CalendarEvent(**values)
        self.session.add(event)
        return event

    def update(self, event: CalendarEvent, **values) -> CalendarEvent:
        for key, value in values.items():
            setattr(event, key, value)
        return event

    def delete(self, event: CalendarEvent) -> None:
        self.session.delete(event)
