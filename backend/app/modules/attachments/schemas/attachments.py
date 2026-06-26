"""Attachment schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AttachmentUpdateRequest(BaseModel):
    """Editable attachment metadata."""

    display_name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1000)


class AttachmentResponse(BaseModel):
    """Attachment metadata response."""

    id: int
    context: str
    group_id: int | None
    beneficiary_id: int | None
    volunteer_id: int | None
    period: str | None
    display_name: str
    description: str
    original_filename: str
    storage_backend: str
    content_type: str
    size_bytes: int
    checksum_sha256: str
    created_by_id: int | None
    created_by_username: str | None
    updated_by_id: int | None
    updated_by_username: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BOCardAttachmentOverview(AttachmentResponse):
    """BO-card metadata enriched for the cross-group management panel."""

    group_name: str | None
    beneficiary_name: str | None
    volunteer_name: str | None


class BOCardAttachmentListResponse(BaseModel):
    """Paginated BO-card overview response."""

    items: list[BOCardAttachmentOverview]
    total: int
    skip: int
    limit: int
