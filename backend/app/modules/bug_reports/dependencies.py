"""Dependencies for the bug reports module."""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_attachment_storage, get_db
from app.infrastructure.storage.attachments import AttachmentStorage
from app.modules.bug_reports.repositories.bug_reports import BugReportRepository
from app.modules.bug_reports.services.bug_reports import BugReportService


def get_bug_report_repository(
    session: Session = Depends(get_db),
) -> BugReportRepository:
    return BugReportRepository(session)


def get_bug_report_service(
    repo: BugReportRepository = Depends(get_bug_report_repository),
    storage: AttachmentStorage = Depends(get_attachment_storage),
) -> BugReportService:
    """Get bug report service dependency."""
    return BugReportService(repo, storage)
