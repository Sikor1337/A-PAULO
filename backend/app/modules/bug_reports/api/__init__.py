"""Bug reports API endpoints."""

from fastapi import APIRouter

from app.modules.bug_reports.api.bug_reports import router as bug_reports_router

router = APIRouter()
router.include_router(bug_reports_router)

__all__ = ["router"]
