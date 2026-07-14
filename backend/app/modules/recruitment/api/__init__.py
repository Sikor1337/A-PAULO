from fastapi import APIRouter

from app.modules.recruitment.api.beneficiary_recruitment import (
    router as beneficiary_recruitment_router,
)
from app.modules.recruitment.api.departures import router as departures_router
from app.modules.recruitment.api.recruitment import router as recruitment_router

router = APIRouter()
router.include_router(recruitment_router)
router.include_router(departures_router)
router.include_router(beneficiary_recruitment_router)

__all__ = ["router"]
