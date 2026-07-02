"""Attachment API endpoints."""

from collections.abc import Iterator
from typing import Annotated, BinaryIO

from fastapi import APIRouter, Depends, Form, Query, status
from fastapi.responses import FileResponse, StreamingResponse
from starlette.background import BackgroundTask

from app.core.constants import ATTACHMENT_MAX_SIZE_BYTES
from app.modules.attachments.dependencies import get_attachment_service
from app.modules.attachments.schemas import (
    AttachmentResponse,
    AttachmentUpdateRequest,
    BOCardArchiveQuery,
    BOCardAttachmentListQuery,
    BOCardAttachmentListResponse,
    CreateAttachmentRequest,
)
from app.modules.attachments.services import AttachmentService
from app.modules.core_data.models import User
from app.modules.security.dependencies import require_permission
from app.modules.security.models.constants import (
    CAN_MANAGE_ATTACHMENTS,
    CAN_VIEW_ATTACHMENTS,
)

router = APIRouter(prefix="/attachments", tags=["attachments"])


def _iter_file(file: BinaryIO, chunk_size: int = 64 * 1024) -> Iterator[bytes]:
    """Stream a binary file-like object in bounded chunks."""
    while chunk := file.read(chunk_size):
        yield chunk


@router.get("/bo-cards", response_model=BOCardAttachmentListResponse)
def list_bo_card_attachments(
    filters: Annotated[BOCardAttachmentListQuery, Query()],
    service: AttachmentService = Depends(get_attachment_service),
    _user: User = Depends(require_permission(CAN_VIEW_ATTACHMENTS)),
):
    """List BO-card metadata with optional filters, sorting, and paging."""
    items, total = service.list_bo_cards(**filters.model_dump())
    return {
        "items": items,
        "total": total,
        "skip": filters.skip,
        "limit": filters.limit,
    }


@router.get("/bo-cards/download")
def download_bo_card_attachments(
    filters: Annotated[BOCardArchiveQuery, Query()],
    service: AttachmentService = Depends(get_attachment_service),
    _user: User = Depends(require_permission(CAN_VIEW_ATTACHMENTS)),
):
    """Download a ZIP archive with all BO cards matching filters."""
    archive, included_count = service.build_bo_cards_archive(**filters.model_dump())
    filename = service.archive_filename()
    return StreamingResponse(
        _iter_file(archive),
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-BO-Cards-Included": str(included_count),
        },
        background=BackgroundTask(archive.close),
    )


@router.post(
    "/bo-cards",
    response_model=AttachmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_bo_card_attachment(
    request: Annotated[CreateAttachmentRequest, Form()],
    service: AttachmentService = Depends(get_attachment_service),
    user: User = Depends(require_permission(CAN_MANAGE_ATTACHMENTS)),
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
    _user: User = Depends(require_permission(CAN_VIEW_ATTACHMENTS)),
):
    """Get attachment metadata."""
    return service.get_attachment_by_id(attachment_id)


@router.get("/{attachment_id}/content")
def get_attachment_content(
    attachment_id: int,
    service: AttachmentService = Depends(get_attachment_service),
    _user: User = Depends(require_permission(CAN_VIEW_ATTACHMENTS)),
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
    user: User = Depends(require_permission(CAN_MANAGE_ATTACHMENTS)),
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
    _user: User = Depends(require_permission(CAN_MANAGE_ATTACHMENTS)),
):
    """Delete attachment metadata and stored file."""
    service.delete_attachment(attachment_id)
    return {"message": "Attachment deleted successfully"}
