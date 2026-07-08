"""Bug reports Pydantic schemas."""

from app.modules.bug_reports.schemas.bug_reports import (
    BugReportCreateRequest,
    BugReportResponse,
    BugReportUpdateRequest,
)

__all__ = ["BugReportCreateRequest", "BugReportResponse", "BugReportUpdateRequest"]
