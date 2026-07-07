"""Bug report schemas."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class BugReportResponse(BaseModel):
    """Bug report DTO."""

    id: int
    title: str
    description: str
    status: str
    resolution_comment: str
    reporter_id: int | None
    reporter_email: str
    original_filename: str | None
    content_type: str | None
    size_bytes: int | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BugReportUpdateRequest(BaseModel):
    """Developer decision: status change and/or resolution comment."""

    status: str | None = Field(None, max_length=20)
    resolution_comment: str | None = Field(None, max_length=2000)
