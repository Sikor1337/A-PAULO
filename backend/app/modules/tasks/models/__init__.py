"""Task models."""
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.sql.base import Base

TASK_STATUSES = ("DO_ZROBIENIA", "W_TRAKCIE", "ZROBIONE")


class Task(Base):
    """A department task, optionally linked to a calendar event."""

    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(default="")
    status: Mapped[str] = mapped_column(
        String(20), default="DO_ZROBIENIA", index=True
    )
    department_id: Mapped[int] = mapped_column(
        ForeignKey("departments.id", ondelete="CASCADE"), index=True
    )
    event_id: Mapped[int | None] = mapped_column(
        ForeignKey("calendar_events.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
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

    checklist: Mapped[list["TaskChecklistItem"]] = relationship(
        back_populates="task",
        cascade="all, delete-orphan",
        order_by="TaskChecklistItem.position",
    )
    assignees: Mapped[list["TaskAssignee"]] = relationship(
        back_populates="task",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Task {self.id} {self.title}>"


class TaskChecklistItem(Base):
    """A single checkbox on a task's checklist."""

    __tablename__ = "task_checklist_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"), index=True
    )
    label: Mapped[str] = mapped_column(String(300))
    is_done: Mapped[bool] = mapped_column(Boolean, default=False)
    done_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    position: Mapped[int] = mapped_column(Integer, default=0)

    task: Mapped[Task] = relationship(back_populates="checklist")

    def __repr__(self) -> str:
        return f"<TaskChecklistItem {self.id} {self.label}>"


class TaskAssignee(Base):
    """A volunteer assigned to a task."""

    __tablename__ = "task_assignees"
    __table_args__ = (
        UniqueConstraint("task_id", "volunteer_id", name="uq_task_volunteer"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id: Mapped[int] = mapped_column(
        ForeignKey("tasks.id", ondelete="CASCADE"), index=True
    )
    volunteer_id: Mapped[int] = mapped_column(
        ForeignKey("volunteers.id", ondelete="CASCADE"), index=True
    )

    task: Mapped[Task] = relationship(back_populates="assignees")

    def __repr__(self) -> str:
        return f"<TaskAssignee task={self.task_id} volunteer={self.volunteer_id}>"
