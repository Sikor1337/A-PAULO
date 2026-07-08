"""Bug report business logic."""

from pathlib import Path

from app.core.errors import NotFoundError, ValidationException
from app.infrastructure.storage.attachments import AttachmentStorage
from app.modules.bug_reports.models.bug_reports import BUG_REPORT_STATUSES, BugReport
from app.modules.bug_reports.repositories.bug_reports import BugReportRepository
from app.modules.core_data.models import User

MAX_FILE_BYTES = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = frozenset(
    {
        ".pdf",
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
        ".heic",
        ".heif",
        ".txt",
        ".log",
        ".zip",
    }
)
STORAGE_CONTEXT = "bug_reports"


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

    def list_reports(self, status: str | None = None) -> list[BugReport]:
        if status and status not in BUG_REPORT_STATUSES:
            raise ValidationException(
                f"Status musi być jednym z: {', '.join(BUG_REPORT_STATUSES)}"
            )
        return self.repo.list_all(status=status)

    def list_my_reports(self, reporter: User) -> list[BugReport]:
        return self.repo.list_for_reporter(reporter.id)

    def create_report(
        self,
        reporter: User,
        *,
        title: str,
        description: str = "",
        filename: str | None = None,
        content: bytes | None = None,
        content_type: str | None = None,
    ) -> BugReport:
        title = title.strip()
        if not title:
            raise ValidationException("Tytuł zgłoszenia jest wymagany")
        if len(title) > 200:
            raise ValidationException("Tytuł może mieć najwyżej 200 znaków")

        stored = None
        if content is not None and filename:
            if len(content) > MAX_FILE_BYTES:
                raise ValidationException("Plik jest zbyt duży (maksymalnie 10 MB)")
            extension = Path(filename).suffix.lower()
            if extension not in ALLOWED_EXTENSIONS:
                raise ValidationException(
                    "Niedozwolony typ pliku. Dozwolone: "
                    + ", ".join(sorted(ALLOWED_EXTENSIONS))
                )
            stored = self.storage.save(content, filename, STORAGE_CONTEXT)

        try:
            report = self.repo.create(
                title=title,
                description=description.strip(),
                reporter_id=reporter.id,
                reporter_email=reporter.email or "",
                original_filename=filename if stored else None,
                storage_backend=stored.storage_backend if stored else None,
                storage_key=stored.storage_key if stored else None,
                content_type=content_type if stored else None,
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

    def update_report(self, report_id: int, **kwargs) -> BugReport:
        try:
            report = self.get_report(report_id)
            new_status = kwargs.get("status")
            if new_status and new_status not in BUG_REPORT_STATUSES:
                raise ValidationException(
                    f"Status musi być jednym z: {', '.join(BUG_REPORT_STATUSES)}"
                )
            report = self.repo.update(report, **kwargs)
            self.repo.flush()
            self.repo.refresh(report)
            self.repo.commit(skip_audit=True)
            return report
        except Exception:
            self.repo.rollback()
            raise

    def read_file(self, report_id: int) -> tuple[BugReport, bytes]:
        report = self.get_report(report_id)
        if not report.storage_key:
            raise NotFoundError("To zgłoszenie nie ma załącznika")
        return report, self.storage.read(report.storage_key)
