"""Beneficiaries API endpoints for PI domain."""

from fastapi import APIRouter, Depends, Query

from app.core.audit import AuditReaderPort, EntityType
from app.modules.audit.dependencies import get_audit_reader
from app.modules.audit.schemas import AuditEventResponse
from app.modules.core_data.models import User
from app.modules.pi.dependencies import get_beneficiary_service
from app.modules.pi.schemas.beneficiaries import (
    BeneficiaryCreateRequest,
    BeneficiaryResponse,
    BeneficiaryUpdateRequest,
)
from app.modules.pi.services.beneficiaries import BeneficiaryService
from app.modules.security.dependencies import require_permission
from app.modules.security.models.constants import (
    CAN_MANAGE_BENEFICIARIES,
    CAN_VIEW_BENEFICIARIES,
)

router = APIRouter(prefix="/beneficiaries", tags=["beneficiaries"])


@router.get("", response_model=list[BeneficiaryResponse])
def list_beneficiaries(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    full_name: str | None = Query(None),
    status: str | None = Query(None),
    bo_enrolled: bool | None = Query(None),
    service: BeneficiaryService = Depends(get_beneficiary_service),
    _user: User = Depends(require_permission(CAN_VIEW_BENEFICIARIES)),
):
    """List all beneficiaries with optional filters."""
    beneficiaries, _ = service.list_beneficiaries(
        skip=skip,
        limit=limit,
        full_name=full_name,
        status=status,
        bo_enrolled=bo_enrolled,
    )
    return beneficiaries


@router.post("", response_model=BeneficiaryResponse)
def create_beneficiary(
    request: BeneficiaryCreateRequest,
    service: BeneficiaryService = Depends(get_beneficiary_service),
    user: User = Depends(require_permission(CAN_MANAGE_BENEFICIARIES)),
):
    """Create new beneficiary."""
    return service.create_beneficiary(actor=user, **request.model_dump())


@router.get("/{beneficiary_id}", response_model=BeneficiaryResponse)
def get_beneficiary(
    beneficiary_id: int,
    service: BeneficiaryService = Depends(get_beneficiary_service),
    _user: User = Depends(require_permission(CAN_VIEW_BENEFICIARIES)),
):
    """Get beneficiary by ID."""
    return service.get_beneficiary_by_id(beneficiary_id)


@router.patch("/{beneficiary_id}", response_model=BeneficiaryResponse)
def update_beneficiary(
    beneficiary_id: int,
    request: BeneficiaryUpdateRequest,
    service: BeneficiaryService = Depends(get_beneficiary_service),
    user: User = Depends(require_permission(CAN_MANAGE_BENEFICIARIES)),
):
    """Update beneficiary."""
    # Only update provided fields
    update_data = request.model_dump(exclude_unset=True)
    return service.update_beneficiary(beneficiary_id, actor=user, **update_data)


@router.delete("/{beneficiary_id}")
def delete_beneficiary(
    beneficiary_id: int,
    service: BeneficiaryService = Depends(get_beneficiary_service),
    user: User = Depends(require_permission(CAN_MANAGE_BENEFICIARIES)),
):
    """Delete beneficiary."""
    service.delete_beneficiary(beneficiary_id, actor=user)
    return {"message": "Beneficiary deleted successfully"}


@router.get("/{beneficiary_id}/audit", response_model=list[AuditEventResponse])
def beneficiary_audit_history(
    beneficiary_id: int,
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
    service: BeneficiaryService = Depends(get_beneficiary_service),
    audit: AuditReaderPort = Depends(get_audit_reader),
    _user: User = Depends(require_permission(CAN_VIEW_BENEFICIARIES)),
):
    service.get_beneficiary_by_id(beneficiary_id)
    return audit.get_logs_for_entity(
        EntityType.PI_BENEFICIARY.value,
        str(beneficiary_id),
        limit=limit,
        offset=offset,
    )
