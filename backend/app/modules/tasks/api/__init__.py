"""Tasks API endpoints."""

from fastapi import APIRouter

from app.modules.tasks.api.tasks import router as tasks_router

router = APIRouter()
router.include_router(tasks_router)

__all__ = ["router"]
