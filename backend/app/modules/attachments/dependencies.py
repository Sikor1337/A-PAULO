"""Attachment dependencies."""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.constants import ATTACHMENT_MAX_SIZE_BYTES
from app.core.dependencies import get_attachment_storage, get_db
from app.infrastructure.storage.attachments import AttachmentStorage
from app.modules.attachments.services import AttachmentService


def get_attachment_service(
    session: Session = Depends(get_db),
    storage: AttachmentStorage = Depends(get_attachment_storage),
) -> AttachmentService:
    """Build attachment service with the configured storage backend."""
    return AttachmentService(
        session=session,
        storage=storage,
        max_size_bytes=ATTACHMENT_MAX_SIZE_BYTES,
    )
