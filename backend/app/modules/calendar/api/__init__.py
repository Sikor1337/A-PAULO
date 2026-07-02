from fastapi import APIRouter

from .events import router as events_router
from .feeds import router as feeds_router

router = APIRouter()
router.include_router(events_router)
router.include_router(feeds_router)

__all__ = ["router"]
