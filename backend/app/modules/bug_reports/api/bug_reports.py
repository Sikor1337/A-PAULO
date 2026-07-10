"""Bug reports API endpoints.

Submitting a report requires only a valid session — every user can report.
Browsing and resolving is gated by the bug-report permissions.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Form, Query, Response, status

from app.modules.bug_reports.dependencies import get_bug_report_service
from app.modules.bug_reports.models.bug_reports import BugReportStatus
from app.modules.bug_reports.schemas.bug_reports import (
    BugReportCreateRequest,
    BugReportResponse,
    BugReportUpdateRequest,
)
from app.modules.bug_reports.services.bug_reports import BugReportService
from app.modules.core_data.models import User
from app.modules.security.dependencies import (
    get_current_user,
    get_permission_service,
    require_permission,
)
from app.modules.security.models.constants import (
    CAN_MANAGE_BUG_REPORTS,
    CAN_SUBMIT_BUG_REPORTS,
    CAN_VIEW_BUG_REPORTS,
)
from app.modules.security.services import PermissionService

router = APIRouter(prefix="/bug-reports", tags=["bug-reports"])


@router.post("", response_model=BugReportResponse)
async def submit_bug_report(
    request: Annotated[BugReportCreateRequest, Form()],
    service: BugReportService = Depends(get_bug_report_service),
    user: User = Depends(require_permission(CAN_SUBMIT_BUG_REPORTS)),
):
    """Submit a bug report with an optional file (needs submit permission)."""
    content = await request.file.read() if request.file is not None else None
    return service.create_report(user, request, content)


@router.get("/my", response_model=list[BugReportResponse])
def my_bug_reports(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: BugReportService = Depends(get_bug_report_service),
    user: User = Depends(require_permission(CAN_SUBMIT_BUG_REPORTS)),
):
    """List the current user's own reports."""
    return service.list_my_reports(user, skip=skip, limit=limit)


@router.get("", response_model=list[BugReportResponse])
def list_bug_reports(
    status: BugReportStatus | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: BugReportService = Depends(get_bug_report_service),
    _user: User = Depends(require_permission(CAN_VIEW_BUG_REPORTS)),
):
    """List all reports, optionally filtered by status (developers)."""
    return service.list_reports(status=status, skip=skip, limit=limit)


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
    return service.update_report(report_id, request)


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bug_report(
    report_id: int,
    service: BugReportService = Depends(get_bug_report_service),
    user: User = Depends(get_current_user),
    permissions: PermissionService = Depends(get_permission_service),
):
    """Delete own report; managers delete any report with its attachment."""
    service.delete_report(
        report_id,
        actor=user,
        can_manage=permissions.has_permission(user, CAN_MANAGE_BUG_REPORTS),
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


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
