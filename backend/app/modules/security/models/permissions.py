"""Flexible user groups and permission assignments.

These groups intentionally have no relationship to the PI domain Group model.
"""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.sql.base import Base

security_group_permissions = Table(
    "security_group_permissions",
    Base.metadata,
    Column(
        "group_id",
        Integer,
        ForeignKey("security_groups.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "permission_id",
        Integer,
        ForeignKey("security_permissions.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)

security_user_groups = Table(
    "security_user_groups",
    Base.metadata,
    Column(
        "user_id",
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "group_id",
        Integer,
        ForeignKey("security_groups.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Permission(Base):
    __tablename__ = "security_permissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False, index=True)


class UserGroup(Base):
    __tablename__ = "security_groups"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(
        String(120), unique=True, nullable=False, index=True
    )
    description: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    system_key: Mapped[str | None] = mapped_column(
        String(50), unique=True, nullable=True, index=True
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

    permissions: Mapped[list[Permission]] = relationship(
        secondary=security_group_permissions,
        lazy="selectin",
    )
