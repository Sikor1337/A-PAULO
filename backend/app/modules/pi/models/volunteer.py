"""Volunteer model for PI domain."""
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.sql.base import Base
from app.modules.pi.models.enums import VolunteerStatus


class Volunteer(Base):
    """Volunteer model."""

    __tablename__ = "volunteers"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(200), index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    social_link: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), default=VolunteerStatus.AKTYWNY.value
    )
    join_date: Mapped[datetime] = mapped_column(DateTime)
    notes: Mapped[str] = mapped_column(default="")
    history: Mapped[str] = mapped_column(default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


    def __repr__(self) -> str:
        return f"<Volunteer {self.full_name}>"
