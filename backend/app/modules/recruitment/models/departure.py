"""Database models for volunteer departure interviews."""

from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Boolean, Date, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.sql.base import Base

if TYPE_CHECKING:
    from app.modules.pi.models.volunteer import Volunteer


class DepartureField(Base):
    __tablename__ = "departure_fields"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    label: Mapped[str] = mapped_column(String(250))
    field_type: Mapped[str] = mapped_column(String(30), default="text")
    required: Mapped[bool] = mapped_column(Boolean, default=False)
    placeholder: Mapped[str] = mapped_column(String(250), default="")
    options: Mapped[list] = mapped_column(JSON, default=list)
    position: Mapped[int] = mapped_column(default=0, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class DepartureInterview(Base):
    __tablename__ = "departure_interviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    volunteer_id: Mapped[int] = mapped_column(
        ForeignKey("volunteers.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
        index=True,
    )
    departure_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    departure_reason: Mapped[str] = mapped_column(Text)
    stay_in_contact: Mapped[bool] = mapped_column(Boolean, default=False)
    answers: Mapped[list] = mapped_column(JSON, default=list)
    completed_by_id: Mapped[int | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    volunteer: Mapped["Volunteer"] = relationship()
