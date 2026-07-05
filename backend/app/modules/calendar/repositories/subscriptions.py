"""Persistence operations for calendar feed tokens and audit entries."""

from sqlalchemy.orm import Session

from app.infrastructure.sql.repository import SQLRepository
from app.modules.calendar.models import CalendarAudit, CalendarFeedToken


class CalendarFeedTokenRepository(SQLRepository):
    def __init__(self, session: Session):
        self.session = session

    def get_by_user_id(self, user_id: int) -> CalendarFeedToken | None:
        return self.session.query(CalendarFeedToken).filter_by(user_id=user_id).first()

    def get_active_by_hash(self, token_hash: str) -> CalendarFeedToken | None:
        return (
            self.session.query(CalendarFeedToken)
            .filter_by(token_hash=token_hash, is_active=True)
            .first()
        )

    def create(self, **values) -> CalendarFeedToken:
        token = CalendarFeedToken(**values)
        self.session.add(token)
        return token


class CalendarAuditRepository(SQLRepository):
    def __init__(self, session: Session):
        self.session = session

    def add(
        self,
        *,
        actor_id: int | None,
        action: str,
        entity_type: str,
        event_id: int | None = None,
        changes: dict | None = None,
    ) -> CalendarAudit:
        entry = CalendarAudit(
            actor_id=actor_id,
            event_id=event_id,
            action=action,
            entity_type=entity_type,
            changes=changes,
        )
        self.session.add(entry)
        return entry
