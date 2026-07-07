"""Bug report repository."""

from sqlalchemy.orm import Session

from app.infrastructure.sql.repository import SQLRepository
from app.modules.bug_reports.models import BugReport


class BugReportRepository(SQLRepository):
    """Data access for bug reports."""

    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, report_id: int) -> BugReport | None:
        return (
            self.session.query(BugReport).filter(BugReport.id == report_id).first()
        )

    def list_all(self, status: str | None = None) -> list[BugReport]:
        query = self.session.query(BugReport)
        if status:
            query = query.filter(BugReport.status == status)
        return query.order_by(BugReport.created_at.desc()).all()

    def list_for_reporter(self, reporter_id: int) -> list[BugReport]:
        return (
            self.session.query(BugReport)
            .filter(BugReport.reporter_id == reporter_id)
            .order_by(BugReport.created_at.desc())
            .all()
        )

    def create(self, **kwargs) -> BugReport:
        report = BugReport(**kwargs)
        self.session.add(report)
        return report

    def update(self, report: BugReport, **kwargs) -> BugReport:
        for key, value in kwargs.items():
            if hasattr(report, key):
                setattr(report, key, value)
        return report
