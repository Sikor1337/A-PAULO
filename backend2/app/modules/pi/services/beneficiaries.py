"""Beneficiary service for PI domain."""
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError
from app.modules.pi.models.beneficiary import Beneficiary
from app.modules.pi.models.group import Group
from app.modules.pi.repositories.beneficiaries import BeneficiaryRepository


class BeneficiaryService:
    """Service for beneficiary operations."""

    def __init__(self, session: Session):
        self.session = session
        self.repo = BeneficiaryRepository(session)

    def _enrich_beneficiary(self, beneficiary: Beneficiary) -> Beneficiary:
        """Enrich beneficiary with group_name computed field."""
        if beneficiary.group_id:
            group_name = self.session.query(Group.name).filter(Group.id == beneficiary.group_id).first()
            beneficiary.group_name = group_name[0] if group_name else None
        else:
            beneficiary.group_name = None
        return beneficiary

    def get_beneficiary_by_id(self, beneficiary_id: int) -> Beneficiary:
        """Get beneficiary by ID or raise NotFoundError."""
        beneficiary = self.repo.get_by_id(beneficiary_id)
        if not beneficiary:
            raise NotFoundError(f"Beneficiary with ID {beneficiary_id} not found")
        return self._enrich_beneficiary(beneficiary)

    def list_beneficiaries(
        self, skip: int = 0, limit: int = 100, full_name: str = None, status: str = None, bo_enrolled: bool = None
    ):
        """List beneficiaries with pagination and filters."""
        beneficiaries = self.repo.list_all(
            skip=skip, limit=limit, full_name=full_name, status=status, bo_enrolled=bo_enrolled
        )
        count = self.repo.count(full_name=full_name, status=status, bo_enrolled=bo_enrolled)
        
        # Enrich each beneficiary with computed fields
        beneficiaries = [self._enrich_beneficiary(b) for b in beneficiaries]
        return beneficiaries, count

    def create_beneficiary(self, **kwargs) -> Beneficiary:
        """Create new beneficiary."""
        try:
            beneficiary = self.repo.create(**kwargs)
            self.session.flush()
            self.session.refresh(beneficiary)
            self.session.commit()
            return self._enrich_beneficiary(beneficiary)
        except Exception:
            self.session.rollback()
            raise

    def update_beneficiary(self, beneficiary_id: int, **kwargs) -> Beneficiary:
        """Update beneficiary."""
        try:
            beneficiary = self.get_beneficiary_by_id(beneficiary_id)
            beneficiary = self.repo.update(beneficiary, **kwargs)
            self.session.flush()
            self.session.refresh(beneficiary)
            self.session.commit()
            return self._enrich_beneficiary(beneficiary)
        except Exception:
            self.session.rollback()
            raise

    def delete_beneficiary(self, beneficiary_id: int) -> None:
        """Delete beneficiary."""
        try:
            beneficiary = self.get_beneficiary_by_id(beneficiary_id)
            self.repo.delete(beneficiary)
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise
