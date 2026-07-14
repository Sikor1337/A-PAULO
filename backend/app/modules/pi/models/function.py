"""Function model for volunteer responsibilities."""

from datetime import datetime
from enum import StrEnum

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    String,
    Table,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.sql.base import Base


class SystemFunctionKey(StrEnum):
    """Stable identifiers for functions calculated by application rules."""

    GROUP_GUIDE = "GROUP_GUIDE"
    BENEFICIARY_LEADER = "BENEFICIARY_LEADER"


volunteer_function = Table(
    "volunteer_function",
    Base.metadata,
    Column(
        "volunteer_id",
        ForeignKey("volunteers.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "function_id", ForeignKey("functions.id", ondelete="CASCADE"), primary_key=True
    ),
)


class Function(Base):
    """Volunteer responsibility assigned manually or by system rules."""

    __tablename__ = "functions"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    system_key: Mapped[str | None] = mapped_column(
        String(50), unique=True, nullable=True, index=True
    )
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
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
        return f"<Function {self.name}>"
