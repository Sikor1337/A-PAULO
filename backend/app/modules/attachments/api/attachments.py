"""Attachment API endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, Form, Query, status
from fastapi.responses import FileResponse

from app.core.constants import ATTACHMENT_MAX_SIZE_BYTES
from app.modules.attachments.dependencies import get_attachment_service
from app.modules.attachments.schemas import (
    AttachmentResponse,
    AttachmentUpdateRequest,
    BOCardAttachmentListQuery,
    CreateAttachmentRequest,
)
from app.modules.attachments.services import AttachmentService
from app.modules.core_data.models import User
from app.modules.security.dependencies import get_current_user

router = APIRouter(prefix="/attachments", tags=["attachments"])


@router.get("/bo-cards", response_model=list[AttachmentResponse])
def list_bo_card_attachments(
    filters: Annotated[BOCardAttachmentListQuery, Query()],
    service: AttachmentService = Depends(get_attachment_service),
    _user: User = Depends(get_current_user),
):
    """List BO-card attachment metadata without file contents."""
    return service.list_bo_cards(**filters.model_dump())


@router.post(
    "/bo-cards",
    response_model=AttachmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_bo_card_attachment(
    request: Annotated[CreateAttachmentRequest, Form()],
    service: AttachmentService = Depends(get_attachment_service),
    user: User = Depends(get_current_user),
):
    """Upload a BO-card file and metadata as multipart form data."""
    content = await request.content.read(ATTACHMENT_MAX_SIZE_BYTES + 1)
    await request.content.close()
    payload = request.model_dump(exclude={"content"})
    return service.create_bo_card(
        actor=user,
        content=content,
        filename=request.filename,
        content_type=request.content_type,
        **payload,
    )


@router.get("/{attachment_id}", response_model=AttachmentResponse)
def get_attachment(
    attachment_id: int,
    service: AttachmentService = Depends(get_attachment_service),
    _user: User = Depends(get_current_user),
):
    """Get attachment metadata."""
    return service.get_attachment_by_id(attachment_id)


@router.get("/{attachment_id}/content")
def get_attachment_content(
    attachment_id: int,
    service: AttachmentService = Depends(get_attachment_service),
    _user: User = Depends(get_current_user),
):
    """View or download attachment content."""
    attachment, path = service.get_file_path(attachment_id)
    return FileResponse(
        path,
        media_type=attachment.content_type,
        filename=attachment.display_name,
        content_disposition_type="inline",
    )


@router.patch("/{attachment_id}", response_model=AttachmentResponse)
def update_attachment(
    attachment_id: int,
    request: AttachmentUpdateRequest,
    service: AttachmentService = Depends(get_attachment_service),
    user: User = Depends(get_current_user),
):
    """Update editable attachment metadata."""
    return service.update_attachment(
        attachment_id,
        actor=user,
        **request.model_dump(exclude_unset=True),
    )


@router.delete("/{attachment_id}")
def delete_attachment(
    attachment_id: int,
    service: AttachmentService = Depends(get_attachment_service),
    _user: User = Depends(get_current_user),
):
    """Delete attachment metadata and stored file."""
    service.delete_attachment(attachment_id)
    return {"message": "Attachment deleted successfully"}
