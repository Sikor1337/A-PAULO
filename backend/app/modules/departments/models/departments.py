"""Department models.

Departments are archived, never hard-deleted, so member history survives.
"""
from datetime import date, datetime
from enum import StrEnum

from sqlalchemy import Date, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.sql.base import Base


class MembershipStatus(StrEnum):
    """Lifecycle of a department membership (PAP-91).

    PENDING — the volunteer asked to join and awaits approval.
    ACTIVE  — a full member (approved, or added directly by a manager).
    """

    PENDING = "PENDING"
    ACTIVE = "ACTIVE"


class Department(Base):
    """A department workspace (e.g. Dział Porządkowy)."""

    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    icon: Mapped[str] = mapped_column(String(16), default="")
    description: Mapped[str] = mapped_column(default="")
    is_archived: Mapped[bool] = mapped_column(default=False)
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
        return f"<Department {self.name}>"


class DepartmentMember(Base):
    """A volunteer's membership in a department."""

    __tablename__ = "department_members"
    __table_args__ = (
        UniqueConstraint(
            "department_id", "volunteer_id", name="uq_department_volunteer"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    department_id: Mapped[int] = mapped_column(
        ForeignKey("departments.id", ondelete="CASCADE"), index=True
    )
    volunteer_id: Mapped[int] = mapped_column(
        ForeignKey("volunteers.id", ondelete="CASCADE"), index=True
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=MembershipStatus.ACTIVE.value,
        server_default=MembershipStatus.ACTIVE.value,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    def __repr__(self) -> str:
        return (
            f"<DepartmentMember dept={self.department_id} "
            f"volunteer={self.volunteer_id}>"
        )


class DepartmentInventoryItem(Base):
    """One item stored in a department warehouse (PAP-92)."""

    __tablename__ = "department_inventory_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    department_id: Mapped[int] = mapped_column(
        ForeignKey("departments.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    location: Mapped[str] = mapped_column(String(300), nullable=False)
    borrowed_by_volunteer_id: Mapped[int | None] = mapped_column(
        ForeignKey("volunteers.id", ondelete="SET NULL"), nullable=True, index=True
    )
    borrowed_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
