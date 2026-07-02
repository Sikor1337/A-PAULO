"""Security API endpoints."""

from fastapi import APIRouter

from .auth import router as auth_router
from .permissions import router as permissions_router

router = APIRouter()
router.include_router(auth_router)
router.include_router(permissions_router, prefix="/api/v1")

__all__ = ["router"]
