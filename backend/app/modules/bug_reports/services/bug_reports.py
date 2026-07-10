"""Bug report business logic."""

from pathlib import Path

from app.core.constants import (
    BUG_REPORT_CONTEXT,
    BUG_REPORT_MAX_FILE_BYTES,
)
from app.core.errors import NotFoundError, PermissionError, ValidationException
from app.core.filetypes import content_matches_extension
from app.core.uploads import ensure_upload_size
from app.infrastructure.storage.attachments import AttachmentStorage
from app.modules.bug_reports.models.bug_reports import BugReport, BugReportStatus
from app.modules.bug_reports.repositories.bug_reports import BugReportRepository
from app.modules.bug_reports.schemas.bug_reports import (
    BugReportCreateRequest,
    BugReportUpdateRequest,
)
from app.modules.core_data.models import User


class BugReportService:
    """Submit, browse and resolve bug reports."""

    def __init__(self, repo: BugReportRepository, storage: AttachmentStorage):
        self.repo = repo
        self.storage = storage

    def get_report(self, report_id: int) -> BugReport:
        report = self.repo.get_by_id(report_id)
        if not report:
            raise NotFoundError("Zgłoszenie nie istnieje")
        return report

    def list_reports(
        self,
        status: BugReportStatus | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[BugReport]:
        return self.repo.list_all(
            status=status.value if status else None, skip=skip, limit=limit
        )

    def list_my_reports(
        self, reporter: User, skip: int = 0, limit: int = 100
    ) -> list[BugReport]:
        return self.repo.list_for_reporter(reporter.id, skip=skip, limit=limit)

    def create_report(
        self,
        reporter: User,
        request: BugReportCreateRequest,
        content: bytes | None = None,
    ) -> BugReport:
        """Persist a report; the optional file goes to attachment storage."""
        filename = request.file.filename if request.file else None
        stored = None
        if content is not None and filename:
            self._validate_file_content(filename, content)
            stored = self.storage.save(content, filename, BUG_REPORT_CONTEXT)

        try:
            report = self.repo.create(
                title=request.title,
                description=request.description,
                reporter_id=reporter.id,
                reporter_email=reporter.email or "",
                original_filename=filename if stored else None,
                storage_backend=stored.storage_backend if stored else None,
                storage_key=stored.storage_key if stored else None,
                content_type=(
                    request.file.content_type if stored and request.file else None
                ),
                size_bytes=len(content) if stored and content is not None else None,
            )
            self.repo.flush()
            self.repo.refresh(report)
            self.repo.commit(skip_audit=True)
            return report
        except Exception:
            self.repo.rollback()
            if stored:
                self.storage.delete(stored.storage_key)
            raise

    def update_report(
        self, report_id: int, request: BugReportUpdateRequest
    ) -> BugReport:
        try:
            report = self.get_report(report_id)
            updates: dict[str, str] = {}
            if request.status is not None:
                updates["status"] = request.status.value
            if request.resolution_comment is not None:
                updates["resolution_comment"] = request.resolution_comment
            report = self.repo.update(report, **updates)
            self.repo.flush()
            self.repo.refresh(report)
            self.repo.commit(skip_audit=True)
            return report
        except Exception:
            self.repo.rollback()
            raise

    def delete_report(self, report_id: int, actor: User, can_manage: bool) -> None:
        """Delete a report together with its stored attachment (PAP-94).

        Reporters may delete their own reports; CAN_MANAGE_BUG_REPORTS
        holders may delete any report.
        """
        report = self.get_report(report_id)
        if not can_manage and report.reporter_id != actor.id:
            raise PermissionError("Możesz usunąć tylko własne zgłoszenie")
        storage_key = report.storage_key
        try:
            self.repo.delete(report)
            self.repo.flush()
            self.repo.commit(skip_audit=True)
        except Exception:
            self.repo.rollback()
            raise
        # Remove the file only after the DB delete committed, so a failed
        # transaction never leaves a report pointing at a missing file.
        if storage_key:
            self.storage.delete(storage_key)

    def read_file(self, report_id: int) -> tuple[BugReport, bytes]:
        report = self.get_report(report_id)
        if not report.storage_key:
            raise NotFoundError("To zgłoszenie nie ma załącznika")
        return report, self.storage.read(report.storage_key)

    @staticmethod
    def _validate_file_content(filename: str, content: bytes) -> None:
        """Re-check real byte size and sniff magic bytes against the extension.

        The schema already validated declared size and extension, but only the
        actual content proves the file is what its extension claims.
        """
        ensure_upload_size(content, BUG_REPORT_MAX_FILE_BYTES)
        extension = Path(filename).suffix.lower()
        if not content_matches_extension(extension, content):
            raise ValidationException(
                "Zawartość pliku nie zgadza się z jego rozszerzeniem"
            )
