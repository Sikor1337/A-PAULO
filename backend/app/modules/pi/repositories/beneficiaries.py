"""Beneficiary repository for PI domain."""

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.infrastructure.sql.repository import SQLRepository
from app.modules.pi.models.beneficiary import Beneficiary
from app.modules.pi.models.group import Group
from app.modules.pi.schemas.beneficiaries import (
    BeneficiaryCreateRequest,
    BeneficiaryUpdateRequest,
)


class BeneficiaryRepository(SQLRepository):
    """Repository for Beneficiary model database operations."""

    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, beneficiary_id: int) -> Beneficiary | None:
        """Get beneficiary by ID."""
        return (
            self.session.query(Beneficiary)
            .filter(Beneficiary.id == beneficiary_id)
            .first()
        )

    def list_full_names(self) -> list[str]:
        """List all beneficiary names (for bulk-import duplicate checks)."""
        return [row[0] for row in self.session.query(Beneficiary.full_name).all()]

    def group_name(self, group_id: int) -> str | None:
        row = self.session.query(Group.name).filter(Group.id == group_id).first()
        return row[0] if row else None

    def list_all(
        self,
        skip: int = 0,
        limit: int = 100,
        full_name: str | None = None,
        status: str | None = None,
        bo_enrolled: bool | None = None,
    ) -> list[Beneficiary]:
        """List beneficiaries with optional filters."""
        query = self.session.query(Beneficiary)

        if full_name:
            query = query.filter(Beneficiary.full_name.ilike(f"%{full_name}%"))
        if status:
            query = query.filter(Beneficiary.status == status)
        if bo_enrolled is not None:
            query = query.filter(Beneficiary.bo_enrolled == bo_enrolled)

        return query.order_by(Beneficiary.full_name).offset(skip).limit(limit).all()

    def count(
        self,
        full_name: str | None = None,
        status: str | None = None,
        bo_enrolled: bool | None = None,
    ) -> int:
        """Count beneficiaries with optional filters."""
        query = self.session.query(func.count(Beneficiary.id))

        if full_name:
            query = query.filter(Beneficiary.full_name.ilike(f"%{full_name}%"))
        if status:
            query = query.filter(Beneficiary.status == status)
        if bo_enrolled is not None:
            query = query.filter(Beneficiary.bo_enrolled == bo_enrolled)

        return query.scalar() or 0

    def create(self, request: BeneficiaryCreateRequest) -> Beneficiary:
        """Create new beneficiary."""
        beneficiary = Beneficiary(
            full_name=request.full_name,
            address=request.address,
            phone=request.phone,
            family_phone=request.family_phone,
            description=request.description,
            group_id=request.group_id,
            status=request.status,
            bo_enrolled=request.bo_enrolled,
            last_priest_visit=request.last_priest_visit,
            last_volunteer_meeting=request.last_volunteer_meeting,
            history=request.history,
        )
        self.session.add(beneficiary)
        return beneficiary

    def update(
        self, beneficiary: Beneficiary, request: BeneficiaryUpdateRequest
    ) -> Beneficiary:
        """Update beneficiary."""
        fields = request.model_fields_set
        if "full_name" in fields and request.full_name is not None:
            beneficiary.full_name = request.full_name
        if "address" in fields and request.address is not None:
            beneficiary.address = request.address
        if "phone" in fields:
            beneficiary.phone = request.phone
        if "family_phone" in fields:
            beneficiary.family_phone = request.family_phone
        if "description" in fields and request.description is not None:
            beneficiary.description = request.description
        if "group_id" in fields:
            beneficiary.group_id = request.group_id
        if "status" in fields and request.status is not None:
            beneficiary.status = request.status
        if "bo_enrolled" in fields and request.bo_enrolled is not None:
            beneficiary.bo_enrolled = request.bo_enrolled
        if "last_priest_visit" in fields:
            beneficiary.last_priest_visit = request.last_priest_visit
        if "last_volunteer_meeting" in fields:
            beneficiary.last_volunteer_meeting = request.last_volunteer_meeting
        if "history" in fields and request.history is not None:
            beneficiary.history = request.history
        return beneficiary

    def delete(self, beneficiary: Beneficiary) -> None:
        """Delete beneficiary."""
        self.session.delete(beneficiary)
