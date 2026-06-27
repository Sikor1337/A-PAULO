"""Attachment dependencies."""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.dependencies import get_attachment_storage, get_db
from app.modules.attachments.services import AttachmentService
from app.modules.attachments.storage import AttachmentStorage


def get_attachment_service(
    session: Session = Depends(get_db),
    storage: AttachmentStorage = Depends(get_attachment_storage),
) -> AttachmentService:
    """Build attachment service with the configured storage backend."""
    settings = get_settings()
    return AttachmentService(
        session=session,
        storage=storage,
        max_size_bytes=settings.attachment_max_size_bytes,
    )
