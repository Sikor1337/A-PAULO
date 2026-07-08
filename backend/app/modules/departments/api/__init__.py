"""Departments API endpoints."""

from fastapi import APIRouter

from app.modules.departments.api.departments import router as departments_router

router = APIRouter()
router.include_router(departments_router)

__all__ = ["router"]
