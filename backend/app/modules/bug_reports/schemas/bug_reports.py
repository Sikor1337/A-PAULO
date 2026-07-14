"""Bug report schemas."""

from datetime import datetime
from pathlib import Path
from typing import Self

from fastapi import UploadFile
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.constants import (
    BUG_REPORT_ALLOWED_EXTENSIONS,
    BUG_REPORT_MAX_FILE_BYTES,
    MEGABYTE,
)
from app.modules.bug_reports.models.bug_reports import BugReportStatus


class BugReportCreateRequest(BaseModel):
    """Multipart bug-report submission: title, description, optional file."""

    title: str = Field(min_length=1, max_length=200)
    description: str = ""
    file: UploadFile | None = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("title", "description", mode="before")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        return value.strip() if isinstance(value, str) else value

    @model_validator(mode="after")
    def validate_file(self) -> Self:
        """Validate the optional attachment's size and extension."""
        if self.file is None or not self.file.filename:
            return self
        if self.file.size and self.file.size > BUG_REPORT_MAX_FILE_BYTES:
            raise ValueError(
                "Plik jest zbyt duży "
                f"(maksymalnie {BUG_REPORT_MAX_FILE_BYTES // MEGABYTE} MB)"
            )
        if Path(self.file.filename).suffix.lower() not in BUG_REPORT_ALLOWED_EXTENSIONS:
            raise ValueError(
                "Niedozwolony typ pliku. Dozwolone: "
                + ", ".join(sorted(BUG_REPORT_ALLOWED_EXTENSIONS))
            )
        return self


class BugReportUpdateRequest(BaseModel):
    """Developer decision: status change and/or resolution comment."""

    status: BugReportStatus | None = None
    resolution_comment: str | None = Field(None, max_length=2000)


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
