"""Database models for the volunteer recruitment workflow."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.sql.base import Base

if TYPE_CHECKING:
    from app.modules.core_data.models import User


class RecruitmentField(Base):
    """A configurable question displayed in the public recruitment form."""

    __tablename__ = "recruitment_fields"

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    label: Mapped[str] = mapped_column(String(250))
    field_type: Mapped[str] = mapped_column(String(30), default="text")
    required: Mapped[bool] = mapped_column(Boolean, default=False)
    placeholder: Mapped[str] = mapped_column(String(250), default="")
    options: Mapped[list] = mapped_column(JSON, default=list)
    position: Mapped[int] = mapped_column(Integer, default=0, index=True)
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


class RecruitmentSubmission(Base):
    """One candidate application, reopened only after an explicit return."""

    __tablename__ = "recruitment_submissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
        index=True,
    )
    full_name: Mapped[str] = mapped_column(String(200), index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    phone: Mapped[str] = mapped_column(String(30))
    social_link: Mapped[str] = mapped_column(String(500), default="")
    availability: Mapped[str] = mapped_column(Text, default="")
    answers: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(30), default="SUBMITTED", index=True)
    return_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    decision_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    volunteer_id: Mapped[int | None] = mapped_column(
        ForeignKey("volunteers.id", ondelete="SET NULL"), nullable=True, unique=True
    )
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    status_changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    user: Mapped["User"] = relationship()
