"""Beneficiaries API endpoints for PI domain."""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.modules.core_data.models import User
from app.modules.pi.schemas.beneficiaries import (
    BeneficiaryCreateRequest,
    BeneficiaryUpdateRequest,
    BeneficiaryResponse,
)
from app.modules.pi.services.beneficiaries import BeneficiaryService
from app.modules.security.dependencies import get_current_user

router = APIRouter(prefix="/beneficiaries", tags=["beneficiaries"])


@router.get("", response_model=list[BeneficiaryResponse])
def list_beneficiaries(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    full_name: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    bo_enrolled: Optional[bool] = Query(None),
    session: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """List all beneficiaries with optional filters."""
    service = BeneficiaryService(session)
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
    session: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """Create new beneficiary."""
    service = BeneficiaryService(session)
    beneficiary = service.create_beneficiary(**request.model_dump())
    return beneficiary


@router.get("/{beneficiary_id}", response_model=BeneficiaryResponse)
def get_beneficiary(
    beneficiary_id: int,
    session: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """Get beneficiary by ID."""
    service = BeneficiaryService(session)
    beneficiary = service.get_beneficiary_by_id(beneficiary_id)
    return beneficiary


@router.patch("/{beneficiary_id}", response_model=BeneficiaryResponse)
def update_beneficiary(
    beneficiary_id: int,
    request: BeneficiaryUpdateRequest,
    session: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """Update beneficiary."""
    service = BeneficiaryService(session)
    # Only update provided fields
    update_data = request.model_dump(exclude_unset=True)
    beneficiary = service.update_beneficiary(beneficiary_id, **update_data)
    return beneficiary


@router.delete("/{beneficiary_id}")
def delete_beneficiary(
    beneficiary_id: int,
    session: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """Delete beneficiary."""
    service = BeneficiaryService(session)
    service.delete_beneficiary(beneficiary_id)
    return {"message": "Beneficiary deleted successfully"}
