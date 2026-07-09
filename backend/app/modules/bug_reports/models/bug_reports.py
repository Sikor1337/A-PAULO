"""Bug report models."""
from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, validates

from app.infrastructure.sql.base import Base


class BugReportStatus(StrEnum):
    NOWY = "NOWY"
    W_TRAKCIE = "W_TRAKCIE"
    ROZWIAZANY = "ROZWIĄZANY"
    ODRZUCONY = "ODRZUCONY"


class BugReport(Base):
    """A user-submitted bug report with an optional attached file.

    reporter_email is a snapshot so the report stays attributable after the
    account is deleted (reporter_id then goes NULL).
    """

    __tablename__ = "bug_reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(default="")
    status: Mapped[str] = mapped_column(
        String(20), default=BugReportStatus.NOWY.value, index=True
    )
    resolution_comment: Mapped[str] = mapped_column(default="")

    reporter_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    reporter_email: Mapped[str] = mapped_column(String(255), default="")

    original_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    storage_backend: Mapped[str | None] = mapped_column(String(50), nullable=True)
    storage_key: Mapped[str | None] = mapped_column(
        String(500), nullable=True, unique=True
    )
    content_type: Mapped[str | None] = mapped_column(String(127), nullable=True)
    size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)

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

    @validates("status")
    def _validate_status(self, key: str, value: str) -> str:
        """Enforce the status enum at the ORM layer, not only in schemas."""
        return BugReportStatus(value).value

    def __repr__(self) -> str:
        return f"<BugReport {self.id} {self.title}>"
