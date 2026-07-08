"""Bug reports SQLAlchemy models."""

from app.modules.bug_reports.models.bug_reports import (
    BUG_REPORT_STATUSES,
    BugReport,
)

__all__ = ["BUG_REPORT_STATUSES", "BugReport"]
