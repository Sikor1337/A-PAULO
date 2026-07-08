"""SQL implementation of the core audit ports."""

from app.core.audit import AuditEntry
from app.modules.audit.models import AuditEvent
from app.modules.audit.repositories.audit import AuditRepository


class SqlAuditService:
    def __init__(self, repository: AuditRepository):
        self.repository = repository

    def record(self, entry: AuditEntry) -> None:
        self.repository.add(
            AuditEvent(
                entity_type=entry.entity_type,
                entity_id=entry.entity_id,
                action=entry.action,
                actor_id=entry.actor_id,
                actor_display_name=entry.actor_display_name,
                context_type=entry.context_type,
                context_id=entry.context_id,
                changes=entry.changes,
            )
        )
        self.repository.mark_recorded()

    def get_logs_for_entity(
        self,
        entity_type: str,
        entity_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditEvent]:
        return self.repository.get_by_entity(
            entity_type=entity_type,
            entity_id=entity_id,
            limit=limit,
            offset=offset,
        )

    def get_logs_for_context(
        self,
        context_type: str,
        context_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditEvent]:
        return self.repository.get_by_context(
            context_type=context_type,
            context_id=context_id,
            limit=limit,
            offset=offset,
        )

    def get_logs_for_entity_or_context(
        self,
        entity_type: str,
        entity_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditEvent]:
        return self.repository.get_by_entity_or_context(
            entity_type=entity_type,
            entity_id=entity_id,
            limit=limit,
            offset=offset,
        )
