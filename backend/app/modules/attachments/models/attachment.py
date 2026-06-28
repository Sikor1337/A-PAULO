"""Attachment metadata model."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.sql.base import Base


class Attachment(Base):
    """Stored file metadata.

    The binary content is owned by a storage adapter. This table keeps only the
    stable metadata needed by the application and by future cloud storage moves.
    """

    __tablename__ = "attachments"
    __table_args__ = (
        Index(
            "ix_attachments_bo_card_lookup",
            "context",
            "group_id",
            "beneficiary_id",
            "volunteer_id",
            "period",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    context: Mapped[str] = mapped_column(String(50), index=True)
    group_id: Mapped[int | None] = mapped_column(
        ForeignKey("groups.id", ondelete="SET NULL"), nullable=True, index=True
    )
    beneficiary_id: Mapped[int | None] = mapped_column(
        ForeignKey("beneficiaries.id", ondelete="SET NULL"), nullable=True, index=True
    )
    volunteer_id: Mapped[int | None] = mapped_column(
        ForeignKey("volunteers.id", ondelete="SET NULL"), nullable=True, index=True
    )
    period: Mapped[str | None] = mapped_column(String(7), nullable=True, index=True)

    display_name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(String(1000), default="")
    original_filename: Mapped[str] = mapped_column(String(255))
    storage_backend: Mapped[str] = mapped_column(String(50), default="local")
    storage_key: Mapped[str] = mapped_column(String(500), unique=True, index=True)
    content_type: Mapped[str] = mapped_column(String(127))
    size_bytes: Mapped[int] = mapped_column(Integer)
    checksum_sha256: Mapped[str] = mapped_column(String(64))

    created_by_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_by_username: Mapped[str | None] = mapped_column(String(150), nullable=True)
    updated_by_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    updated_by_username: Mapped[str | None] = mapped_column(String(150), nullable=True)
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
        return f"<Attachment {self.id} {self.display_name}>"
