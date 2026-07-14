"""PI API endpoints - volunteer, beneficiary, group, and assignment management."""

from app.modules.pi.api.beneficiaries import router as beneficiaries_router
from app.modules.pi.api.groups import router as groups_router
from app.modules.pi.api.volunteers import router as volunteers_router

__all__ = ["beneficiaries_router", "groups_router", "volunteers_router"]
