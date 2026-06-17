"""Group and assignment models for PI domain."""
from datetime import datetime

from sqlalchemy import (
    String,
    DateTime,
    ForeignKey,
    Boolean,
    Table,
    Column,
    Integer,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.sql.base import Base

# Many-to-many table for Group-Volunteer relationship
group_volunteer = Table(
    "group_volunteer",
    Base.metadata,
    Column("group_id", Integer, ForeignKey("groups.id", ondelete="CASCADE"), primary_key=True),
    Column("volunteer_id", Integer, ForeignKey("volunteers.id", ondelete="CASCADE"), primary_key=True),
)


class Group(Base):
    """Group model."""

    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), index=True)
    leader_id: Mapped[int | None] = mapped_column(
        ForeignKey("volunteers.id", ondelete="SET NULL"), nullable=True
    )
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
        return f"<Group {self.name}>"


class BeneficiaryAssignment(Base):
    """Assignment of volunteer to beneficiary."""

    __tablename__ = "beneficiary_assignments"
    __table_args__ = (
        UniqueConstraint("beneficiary_id", "volunteer_id", name="uq_beneficiary_volunteer"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    beneficiary_id: Mapped[int] = mapped_column(
        ForeignKey("beneficiaries.id", ondelete="CASCADE")
    )
    volunteer_id: Mapped[int] = mapped_column(
        ForeignKey("volunteers.id", ondelete="CASCADE")
    )
    is_main: Mapped[bool] = mapped_column(default=False)
    additional_info: Mapped[str] = mapped_column(default="")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    def __repr__(self) -> str:
        return f"<BeneficiaryAssignment beneficiary_id={self.beneficiary_id} volunteer_id={self.volunteer_id}>"
