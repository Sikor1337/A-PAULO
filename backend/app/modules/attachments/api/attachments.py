"""Attachment API endpoints."""

from typing import Literal

from fastapi import APIRouter, Body, Depends, Query, Request
from fastapi.responses import FileResponse, StreamingResponse

from app.modules.attachments.dependencies import get_attachment_service
from app.modules.attachments.schemas import (
    AttachmentResponse,
    AttachmentUpdateRequest,
    BOCardAttachmentListResponse,
)
from app.modules.attachments.services import AttachmentService
from app.modules.core_data.models import User
from app.modules.security.dependencies import get_current_user

router = APIRouter(prefix="/attachments", tags=["attachments"])


@router.get("/bo-cards/all", response_model=BOCardAttachmentListResponse)
def list_all_bo_card_attachments(
    group_id: int | None = Query(None),
    beneficiary_id: int | None = Query(None),
    volunteer_id: int | None = Query(None),
    period_from: str | None = Query(None),
    period_to: str | None = Query(None),
    search: str | None = Query(None),
    has_comment: bool | None = Query(None),
    sort_by: Literal[
        "created_at",
        "updated_at",
        "period",
        "display_name",
        "group_name",
        "beneficiary_name",
        "volunteer_name",
        "size_bytes",
    ] = Query("created_at"),
    sort_direction: Literal["asc", "desc"] = Query("desc"),
    skip: int = Query(0, ge=0),
    limit: int = Query(25, ge=1, le=100),
    service: AttachmentService = Depends(get_attachment_service),
    _user: User = Depends(get_current_user),
):
    """List all BO-card metadata without file contents."""
    items, total = service.list_bo_cards_overview(
        group_id=group_id,
        beneficiary_id=beneficiary_id,
        volunteer_id=volunteer_id,
        period_from=period_from,
        period_to=period_to,
        search=search,
        has_comment=has_comment,
        sort_by=sort_by,
        sort_direction=sort_direction,
        skip=skip,
        limit=limit,
    )
    return {"items": items, "total": total, "skip": skip, "limit": limit}


@router.get("/bo-cards/all/download")
def download_all_bo_card_attachments(
    group_id: int | None = Query(None),
    beneficiary_id: int | None = Query(None),
    volunteer_id: int | None = Query(None),
    period_from: str | None = Query(None),
    period_to: str | None = Query(None),
    search: str | None = Query(None),
    has_comment: bool | None = Query(None),
    service: AttachmentService = Depends(get_attachment_service),
    _user: User = Depends(get_current_user),
):
    """Download a ZIP archive with all BO cards matching filters."""
    archive, included_count = service.build_bo_cards_archive(
        group_id=group_id,
        beneficiary_id=beneficiary_id,
        volunteer_id=volunteer_id,
        period_from=period_from,
        period_to=period_to,
        search=search,
        has_comment=has_comment,
    )
    filename = service.archive_filename()
    return StreamingResponse(
        iter([archive]),
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "X-BO-Cards-Included": str(included_count),
        },
    )


@router.get("/bo-cards", response_model=list[AttachmentResponse])
def list_bo_card_attachments(
    group_id: int = Query(...),
    beneficiary_id: int | None = Query(None),
    volunteer_id: int | None = Query(None),
    period: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: AttachmentService = Depends(get_attachment_service),
    _user: User = Depends(get_current_user),
):
    """List BO-card attachment metadata without file contents."""
    return service.list_bo_cards(
        group_id=group_id,
        beneficiary_id=beneficiary_id,
        volunteer_id=volunteer_id,
        period=period,
        skip=skip,
        limit=limit,
    )


@router.post("/bo-cards", response_model=AttachmentResponse)
async def create_bo_card_attachment(
    request: Request,
    content: bytes = Body(..., media_type="application/octet-stream"),
    group_id: int = Query(...),
    beneficiary_id: int = Query(...),
    volunteer_id: int = Query(...),
    period: str = Query(...),
    filename: str = Query(...),
    display_name: str | None = Query(None),
    description: str = Query(""),
    service: AttachmentService = Depends(get_attachment_service),
    user: User = Depends(get_current_user),
):
    """Upload a BO-card file as raw request body."""
    content_type = request.headers.get("content-type", "application/octet-stream")
    return service.create_bo_card(
        group_id=group_id,
        beneficiary_id=beneficiary_id,
        volunteer_id=volunteer_id,
        period=period,
        filename=filename,
        content_type=content_type,
        content=content,
        actor=user,
        display_name=display_name,
        description=description,
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
