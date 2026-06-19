"""Beneficiary repository for PI domain."""
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.modules.pi.models.beneficiary import Beneficiary


class BeneficiaryRepository:
    """Repository for Beneficiary model database operations."""

    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, beneficiary_id: int) -> Beneficiary | None:
        """Get beneficiary by ID."""
        return self.session.query(Beneficiary).filter(Beneficiary.id == beneficiary_id).first()

    def list_all(
        self, skip: int = 0, limit: int = 100, full_name: str = None, status: str = None, bo_enrolled: bool = None
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
        self, full_name: str = None, status: str = None, bo_enrolled: bool = None
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

    def create(self, **kwargs) -> Beneficiary:
        """Create new beneficiary."""
        beneficiary = Beneficiary(**kwargs)
        self.session.add(beneficiary)
        return beneficiary

    def update(self, beneficiary: Beneficiary, **kwargs) -> Beneficiary:
        """Update beneficiary."""
        for key, value in kwargs.items():
            if hasattr(beneficiary, key):
                setattr(beneficiary, key, value)
        return beneficiary

    def delete(self, beneficiary: Beneficiary) -> None:
        """Delete beneficiary."""
        self.session.delete(beneficiary)
