"""Attachment dependencies."""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.dependencies import get_db
from app.modules.attachments.services import AttachmentService
from app.modules.attachments.storage import LocalAttachmentStorage


def get_attachment_service(session: Session = Depends(get_db)) -> AttachmentService:
    """Build attachment service with the configured storage backend."""
    settings = get_settings()
    storage = LocalAttachmentStorage(settings.attachment_storage_path)
    return AttachmentService(
        session=session,
        storage=storage,
        max_size_bytes=settings.attachment_max_size_bytes,
    )

