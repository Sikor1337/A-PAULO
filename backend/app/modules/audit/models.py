"""Append-only audit persistence model."""

from datetime import datetime

from sqlalchemy import (
    JSON,
    BigInteger,
    DateTime,
    Identity,
    Index,
    String,
    desc,
    event,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, Mapper, mapped_column

from app.infrastructure.sql.base import Base


class AuditEvent(Base):
    __tablename__ = "audit_events"
    __table_args__ = (
        Index(
            "idx_audit_entity",
            "entity_type",
            "entity_id",
            desc("created_at"),
        ),
        Index(
            "idx_audit_context",
            "context_type",
            "context_id",
            desc("created_at"),
        ),
        Index("idx_audit_actor", "actor_id", desc("created_at")),
        Index("idx_audit_changes_gin", "changes", postgresql_using="gin"),
        {"postgresql_partition_by": "RANGE (created_at)"},
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(255), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    actor_id: Mapped[str] = mapped_column(String(255), nullable=False)
    actor_display_name: Mapped[str | None] = mapped_column(String(255))
    context_type: Mapped[str | None] = mapped_column(String(100))
    context_id: Mapped[str | None] = mapped_column(String(255))
    changes: Mapped[dict] = mapped_column(
        JSON().with_variant(JSONB(), "postgresql"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        primary_key=True,
        nullable=False,
        server_default=func.now(),
    )


def _reject_mutation(mapper: Mapper, connection, target: AuditEvent) -> None:
    raise RuntimeError("Audit events are append-only")


event.listen(AuditEvent, "before_update", _reject_mutation)
event.listen(AuditEvent, "before_delete", _reject_mutation)
