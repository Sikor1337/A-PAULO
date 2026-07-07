"""Bug reports API endpoints.

Submitting a report requires only a valid session — every user can report.
Browsing and resolving is gated by the bug-report permissions.
"""

from fastapi import APIRouter, Depends, File, Form, Query, Response, UploadFile

from app.modules.bug_reports.dependencies import get_bug_report_service
from app.modules.bug_reports.schemas import (
    BugReportResponse,
    BugReportUpdateRequest,
)
from app.modules.bug_reports.services import BugReportService
from app.modules.core_data.models import User
from app.modules.security.dependencies import get_current_user, require_permission
from app.modules.security.models.constants import (
    CAN_MANAGE_BUG_REPORTS,
    CAN_VIEW_BUG_REPORTS,
)

router = APIRouter(prefix="/bug-reports", tags=["bug-reports"])


@router.post("", response_model=BugReportResponse)
async def submit_bug_report(
    title: str = Form(...),
    description: str = Form(""),
    file: UploadFile | None = File(None),
    service: BugReportService = Depends(get_bug_report_service),
    user: User = Depends(get_current_user),
):
    """Submit a bug report with an optional file (any logged-in user)."""
    content = await file.read() if file is not None else None
    return service.create_report(
        user,
        title=title,
        description=description,
        filename=file.filename if file is not None else None,
        content=content,
        content_type=file.content_type if file is not None else None,
    )


@router.get("/my", response_model=list[BugReportResponse])
def my_bug_reports(
    service: BugReportService = Depends(get_bug_report_service),
    user: User = Depends(get_current_user),
):
    """List the current user's own reports."""
    return service.list_my_reports(user)


@router.get("", response_model=list[BugReportResponse])
def list_bug_reports(
    status: str | None = Query(None),
    service: BugReportService = Depends(get_bug_report_service),
    _user: User = Depends(require_permission(CAN_VIEW_BUG_REPORTS)),
):
    """List all reports, optionally filtered by status (developers)."""
    return service.list_reports(status=status)


@router.get("/{report_id}", response_model=BugReportResponse)
def get_bug_report(
    report_id: int,
    service: BugReportService = Depends(get_bug_report_service),
    _user: User = Depends(require_permission(CAN_VIEW_BUG_REPORTS)),
):
    """Get one report (developers)."""
    return service.get_report(report_id)


@router.patch("/{report_id}", response_model=BugReportResponse)
def update_bug_report(
    report_id: int,
    request: BugReportUpdateRequest,
    service: BugReportService = Depends(get_bug_report_service),
    _user: User = Depends(require_permission(CAN_MANAGE_BUG_REPORTS)),
):
    """Change status / add a resolution comment (developers)."""
    update_data = request.model_dump(exclude_unset=True)
    return service.update_report(report_id, **update_data)


@router.get("/{report_id}/file")
def download_bug_report_file(
    report_id: int,
    service: BugReportService = Depends(get_bug_report_service),
    _user: User = Depends(require_permission(CAN_VIEW_BUG_REPORTS)),
):
    """Download the attached file (developers)."""
    report, content = service.read_file(report_id)
    filename = report.original_filename or "zalacznik"
    return Response(
        content=content,
        media_type=report.content_type or "application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
