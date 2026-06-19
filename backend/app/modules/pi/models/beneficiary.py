"""Beneficiary model for PI domain."""
from datetime import datetime, date

from sqlalchemy import String, DateTime, Date, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.sql.base import Base


class Beneficiary(Base):
    """Beneficiary model."""

    __tablename__ = "beneficiaries"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(200), index=True)
    address: Mapped[str] = mapped_column(String(500))
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    family_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    description: Mapped[str] = mapped_column(default="")
    group_id: Mapped[int | None] = mapped_column(
        ForeignKey("groups.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(50), default="OBECNY")  # OBECNY, ZMARŁY, BYŁY, DPS_ZOL
    bo_enrolled: Mapped[bool] = mapped_column(default=False)
    last_priest_visit: Mapped[date | None] = mapped_column(Date, nullable=True)
    last_volunteer_meeting: Mapped[date | None] = mapped_column(Date, nullable=True)
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
        return f"<Beneficiary {self.full_name}>"
