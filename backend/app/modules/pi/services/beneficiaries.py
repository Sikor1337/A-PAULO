"""Beneficiary service for PI domain."""

from app.core.audit import AuditEntry, AuditPort, EntityType, calculate_delta
from app.core.errors import NotFoundError
from app.modules.core_data.models import User
from app.modules.pi.audit_state import beneficiary_audit_state
from app.modules.pi.models.beneficiary import Beneficiary
from app.modules.pi.repositories.beneficiaries import BeneficiaryRepository
from app.modules.pi.schemas.beneficiaries import (
    BeneficiaryCreateRequest,
    BeneficiaryUpdateRequest,
)


class BeneficiaryService:
    """Service for beneficiary operations."""

    def __init__(self, repo: BeneficiaryRepository, audit: AuditPort):
        self.repo = repo
        self.audit = audit

    def _record(
        self,
        action: str,
        beneficiary_id: int,
        actor: User,
        old_state: dict,
        new_state: dict,
    ) -> None:
        self.audit.record(
            AuditEntry(
                entity_type=EntityType.PI_BENEFICIARY.value,
                entity_id=str(beneficiary_id),
                action=action,
                actor_id=str(actor.id),
                actor_display_name=actor.email,
                changes=calculate_delta(old_state, new_state),
            )
        )

    def _enrich_beneficiary(self, beneficiary: Beneficiary) -> Beneficiary:
        """Enrich beneficiary with group_name computed field."""
        if beneficiary.group_id:
            beneficiary.group_name = self.repo.group_name(beneficiary.group_id)
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
        self,
        skip: int = 0,
        limit: int = 100,
        full_name: str | None = None,
        status: str | None = None,
        bo_enrolled: bool | None = None,
    ):
        """List beneficiaries with pagination and filters."""
        beneficiaries = self.repo.list_all(
            skip=skip,
            limit=limit,
            full_name=full_name,
            status=status,
            bo_enrolled=bo_enrolled,
        )
        count = self.repo.count(
            full_name=full_name, status=status, bo_enrolled=bo_enrolled
        )

        # Enrich each beneficiary with computed fields
        beneficiaries = [self._enrich_beneficiary(b) for b in beneficiaries]
        return beneficiaries, count

    def prepare_beneficiary(
        self, actor: User, request: BeneficiaryCreateRequest
    ) -> Beneficiary:
        """Create and audit a beneficiary without committing the transaction."""
        beneficiary = self.repo.create(request)
        self.repo.flush()
        self.repo.refresh(beneficiary)
        self._record(
            "CREATE",
            beneficiary.id,
            actor,
            {},
            beneficiary_audit_state(beneficiary),
        )
        return self._enrich_beneficiary(beneficiary)

    def create_beneficiary(
        self, actor: User, request: BeneficiaryCreateRequest
    ) -> Beneficiary:
        """Create new beneficiary."""
        try:
            beneficiary = self.prepare_beneficiary(actor, request)
            self.repo.commit()
            return beneficiary
        except Exception:
            self.repo.rollback()
            raise

    def update_beneficiary(
        self,
        beneficiary_id: int,
        actor: User,
        request: BeneficiaryUpdateRequest,
    ) -> Beneficiary:
        """Update beneficiary."""
        try:
            beneficiary = self.get_beneficiary_by_id(beneficiary_id)
            old_state = beneficiary_audit_state(beneficiary)
            beneficiary = self.repo.update(beneficiary, request)
            self.repo.flush()
            self.repo.refresh(beneficiary)
            new_state = beneficiary_audit_state(beneficiary)
            changes = calculate_delta(old_state, new_state)
            if not changes:
                # Genuine no-op: persist (nothing changed) without an audit entry.
                self.repo.commit(skip_audit=True)
                return self._enrich_beneficiary(beneficiary)
            self._record("UPDATE", beneficiary.id, actor, old_state, new_state)
            self.repo.commit()
            return self._enrich_beneficiary(beneficiary)
        except Exception:
            self.repo.rollback()
            raise

    def delete_beneficiary(self, beneficiary_id: int, actor: User) -> None:
        """Delete beneficiary."""
        try:
            beneficiary = self.get_beneficiary_by_id(beneficiary_id)
            old_state = beneficiary_audit_state(beneficiary)
            self.repo.delete(beneficiary)
            self._record("DELETE", beneficiary.id, actor, old_state, {})
            self.repo.commit()
        except Exception:
            self.repo.rollback()
            raise
