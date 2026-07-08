"""Append-only audit data access."""

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.infrastructure.sql.repository import SQLRepository
from app.modules.audit.models import AuditEvent


class AuditRepository(SQLRepository):
    def __init__(self, session: Session):
        super().__init__(session)

    def add(self, event: AuditEvent) -> None:
        self.session.add(event)

    def mark_recorded(self) -> None:
        self.session.info["audit_recorded"] = True

    def get_by_entity(
        self,
        entity_type: str,
        entity_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditEvent]:
        return (
            self.session.query(AuditEvent)
            .filter(
                AuditEvent.entity_type == entity_type,
                AuditEvent.entity_id == entity_id,
            )
            .order_by(AuditEvent.created_at.desc(), AuditEvent.id.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def get_by_context(
        self,
        context_type: str,
        context_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditEvent]:
        return (
            self.session.query(AuditEvent)
            .filter(
                AuditEvent.context_type == context_type,
                AuditEvent.context_id == context_id,
            )
            .order_by(AuditEvent.created_at.desc(), AuditEvent.id.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def get_by_entity_or_context(
        self,
        entity_type: str,
        entity_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditEvent]:
        return (
            self.session.query(AuditEvent)
            .filter(
                or_(
                    and_(
                        AuditEvent.entity_type == entity_type,
                        AuditEvent.entity_id == entity_id,
                    ),
                    and_(
                        AuditEvent.context_type == entity_type,
                        AuditEvent.context_id == entity_id,
                    ),
                )
            )
            .order_by(AuditEvent.created_at.desc(), AuditEvent.id.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
