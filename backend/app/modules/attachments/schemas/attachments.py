"""Attachment schemas."""

from datetime import datetime
from pathlib import Path
from typing import Self
from urllib.parse import unquote

from fastapi import UploadFile
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.constants import (
    ATTACHMENT_ALLOWED_CONTENT_TYPES,
    ATTACHMENT_ALLOWED_EXTENSIONS,
    ATTACHMENT_FALLBACK_CONTENT_TYPES,
    ATTACHMENT_MAX_SIZE_BYTES,
    ATTACHMENT_SUPPORTED_FILES_MESSAGE,
    BO_CARD_PERIOD_PATTERN,
    BOCardSortKey,
    SortDirection,
)


class BOCardFilters(BaseModel):
    """Validated filters shared by BO-card listing and archive endpoints."""

    group_id: int | None = Field(None, ge=1)
    beneficiary_id: int | None = Field(None, ge=1)
    volunteer_id: int | None = Field(None, ge=1)
    period: str | None = Field(None, pattern=BO_CARD_PERIOD_PATTERN)
    period_from: str | None = Field(None, pattern=BO_CARD_PERIOD_PATTERN)
    period_to: str | None = Field(None, pattern=BO_CARD_PERIOD_PATTERN)
    search: str | None = Field(None, max_length=255)
    has_comment: bool | None = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("search", mode="before")
    @classmethod
    def normalize_search(cls, value: str | None) -> str | None:
        """Normalize blank searches to an omitted filter."""
        normalized = (value or "").strip()
        return normalized or None

    @model_validator(mode="after")
    def validate_period_range(self) -> Self:
        """Reject an inverted inclusive period range."""
        if self.period_from and self.period_to and self.period_from > self.period_to:
            raise ValueError("Period from cannot be later than period to")
        return self


class BOCardAttachmentListQuery(BOCardFilters):
    """Validated filters, sorting, and paging for BO-card metadata."""

    sort_by: BOCardSortKey = "created_at"
    sort_direction: SortDirection = "desc"
    skip: int = Field(0, ge=0)
    limit: int = Field(100, ge=1, le=1000)


class BOCardArchiveQuery(BOCardFilters):
    """Validated filters for downloading BO-card files as an archive."""


class CreateAttachmentRequest(BaseModel):
    """Validated BO-card multipart request body."""

    content: UploadFile
    group_id: int = Field(ge=1)
    beneficiary_id: int = Field(ge=1)
    volunteer_id: int = Field(ge=1)
    period: str = Field(pattern=BO_CARD_PERIOD_PATTERN)
    display_name: str | None = Field(None, min_length=1, max_length=255)
    description: str = Field("", max_length=1000)

    model_config = ConfigDict(extra="forbid")

    @staticmethod
    def _normalize_filename(value: str | None) -> str:
        decoded = unquote(value or "").strip()
        filename = Path(decoded).name
        if not filename or filename in {".", ".."}:
            raise ValueError("Attachment filename is required")
        return filename[:255]

    @staticmethod
    def _normalize_content_type(value: str | None) -> str:
        return (value or "application/octet-stream").split(";", 1)[0].strip()

    @field_validator("display_name", mode="before")
    @classmethod
    def normalize_display_name(cls, value: str | None) -> str | None:
        """Reject blank display names while preserving an omitted value."""
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            raise ValueError("Attachment display name is required")
        return normalized

    @field_validator("description", mode="before")
    @classmethod
    def normalize_description(cls, value: str | None) -> str:
        """Store descriptions without surrounding whitespace."""
        return (value or "").strip()

    @model_validator(mode="after")
    def validate_file_type(self) -> Self:
        """Validate uploaded file size, filename, and declared MIME type."""
        if not self.content.size:
            raise ValueError("Attachment file cannot be empty")
        if self.content.size > ATTACHMENT_MAX_SIZE_BYTES:
            raise ValueError("Attachment file is too large")

        filename = self._normalize_filename(self.content.filename)
        content_type = self._normalize_content_type(self.content.content_type)
        if Path(filename).suffix.lower() not in ATTACHMENT_ALLOWED_EXTENSIONS:
            raise ValueError(ATTACHMENT_SUPPORTED_FILES_MESSAGE)
        if (
            content_type not in ATTACHMENT_ALLOWED_CONTENT_TYPES
            and content_type not in ATTACHMENT_FALLBACK_CONTENT_TYPES
        ):
            raise ValueError(ATTACHMENT_SUPPORTED_FILES_MESSAGE)
        return self

    @property
    def filename(self) -> str:
        """Return a safe filename derived from multipart metadata."""
        return self._normalize_filename(self.content.filename)

    @property
    def content_type(self) -> str:
        """Return a normalized MIME type derived from multipart metadata."""
        return self._normalize_content_type(self.content.content_type)


class AttachmentUpdateRequest(BaseModel):
    """Editable attachment metadata."""

    display_name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=1000)

    model_config = ConfigDict(extra="forbid")


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
