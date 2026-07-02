"""Database models for events, subscriptions and calendar audit entries."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.sql.base import Base
from app.modules.calendar.models.constants import (
    DEFAULT_TIMEZONE,
    ORGANIZATION_VISIBILITY,
    PUBLISHED_STATUS,
)


class CalendarEvent(Base):
    __tablename__ = "calendar_events"
    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'published', 'cancelled')",
            name="ck_calendar_event_status",
        ),
        CheckConstraint(
            "visibility IN ('organization', 'admins')",
            name="ck_calendar_event_visibility",
        ),
        CheckConstraint("ends_at >= starts_at", name="ck_calendar_event_dates"),
        CheckConstraint("sequence >= 0", name="ck_calendar_event_sequence"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    uid: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, default=lambda: f"{uuid4()}@a-paulo"
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    timezone: Mapped[str] = mapped_column(
        String(64), nullable=False, default=DEFAULT_TIMEZONE
    )
    is_all_day: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    location: Mapped[str] = mapped_column(String(300), nullable=False, default="")
    recurrence_rule: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default=PUBLISHED_STATUS, index=True
    )
    visibility: Mapped[str] = mapped_column(
        String(30), nullable=False, default=ORGANIZATION_VISIBILITY, index=True
    )
    author_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    sequence: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    author = relationship("User", lazy="joined")

    @property
    def author_name(self) -> str:
        full_name = f"{self.author.first_name} {self.author.last_name}".strip()
        return full_name or self.author.email


class CalendarFeedToken(Base):
    __tablename__ = "calendar_feed_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user = relationship("User", lazy="joined")


class CalendarAudit(Base):
    __tablename__ = "calendar_audit"

    id: Mapped[int] = mapped_column(primary_key=True)
    actor_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    event_id: Mapped[int | None] = mapped_column(
        ForeignKey("calendar_events.id", ondelete="SET NULL"), nullable=True, index=True
    )
    action: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(30), nullable=False)
    changes: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
