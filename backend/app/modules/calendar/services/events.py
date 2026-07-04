"""Business rules for calendar events."""

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.errors import NotFoundError, ValidationException
from app.modules.calendar.models import CalendarEvent
from app.modules.calendar.models.constants import (
    ADMIN_VISIBILITY,
    CANCELLED_STATUS,
)
from app.modules.calendar.repositories import (
    CalendarAuditRepository,
    CalendarEventRepository,
)
from app.modules.calendar.schemas import EventCreateRequest, EventUpdateRequest
from app.modules.core_data.models import User
from app.modules.security.models.constants import CAN_MANAGE_EVENTS
from app.modules.security.services.permissions import PermissionService


class CalendarEventService:
    def __init__(self, session: Session):
        self.session = session
        self.events = CalendarEventRepository(session)
        self.audit = CalendarAuditRepository(session)
        self.permissions = PermissionService(session)

    def _can_view(self, event: CalendarEvent, user: User) -> bool:
        return event.visibility != ADMIN_VISIBILITY or self.permissions.has_permission(
            user, CAN_MANAGE_EVENTS
        )

    def list_events(
        self,
        user: User,
        **filters,
    ) -> list[CalendarEvent]:
        return self.events.list_visible(
            is_admin=self.permissions.has_permission(user, CAN_MANAGE_EVENTS),
            **filters,
        )

    def get_event(self, event_id: int, user: User) -> CalendarEvent:
        event = self.events.get_by_id(event_id)
        if not event or not self._can_view(event, user):
            raise NotFoundError("Wydarzenie nie istnieje lub nie masz do niego dostępu")
        return event

    def create_event(self, data: EventCreateRequest, actor: User) -> CalendarEvent:
        try:
            event = self.events.create(author_id=actor.id, **data.model_dump())
            self.session.flush()
            self.audit.add(
                actor_id=actor.id,
                event_id=event.id,
                action="created",
                entity_type="event",
            )
            self.session.commit()
            self.session.refresh(event)
            return event
        except Exception:
            self.session.rollback()
            raise

    def update_event(
        self,
        event_id: int,
        data: EventUpdateRequest,
        actor: User,
    ) -> CalendarEvent:
        try:
            event = self.get_event(event_id, actor)
            values = data.model_dump(exclude_unset=True)
            starts_at = values.get("starts_at", event.starts_at)
            ends_at = values.get("ends_at", event.ends_at)
            if ends_at < starts_at:
                raise ValidationException(
                    "Data zakończenia nie może być wcześniejsza od rozpoczęcia"
                )

            changes = {
                key: {
                    "from": self._json_value(getattr(event, key)),
                    "to": self._json_value(value),
                }
                for key, value in values.items()
                if getattr(event, key) != value
            }
            if not changes:
                return event

            values["sequence"] = event.sequence + 1
            values["updated_at"] = datetime.now(UTC)
            self.events.update(event, **values)
            self.audit.add(
                actor_id=actor.id,
                event_id=event.id,
                action="updated",
                entity_type="event",
                changes=changes,
            )
            self.session.commit()
            self.session.refresh(event)
            return event
        except Exception:
            self.session.rollback()
            raise

    def cancel_event(self, event_id: int, actor: User) -> CalendarEvent:
        try:
            event = self.get_event(event_id, actor)
            if event.status == CANCELLED_STATUS:
                return event
            self.events.update(
                event,
                status=CANCELLED_STATUS,
                sequence=event.sequence + 1,
                updated_at=datetime.now(UTC),
            )
            self.audit.add(
                actor_id=actor.id,
                event_id=event.id,
                action="cancelled",
                entity_type="event",
            )
            self.session.commit()
            self.session.refresh(event)
            return event
        except Exception:
            self.session.rollback()
            raise

    def delete_event(self, event_id: int, actor: User) -> None:
        try:
            event = self.get_event(event_id, actor)
            self.audit.add(
                actor_id=actor.id,
                event_id=event.id,
                action="deleted",
                entity_type="event",
                changes={"uid": event.uid, "title": event.title},
            )
            self.events.delete(event)
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise

    @staticmethod
    def _json_value(value):
        return value.isoformat() if isinstance(value, datetime) else value
