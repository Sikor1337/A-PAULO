"""Volunteer service for PI domain."""

from app.core.audit import AuditEntry, AuditPort, EntityType, calculate_delta
from app.core.errors import ConflictError, NotFoundError
from app.modules.core_data.models import User
from app.modules.pi.audit_state import volunteer_audit_state
from app.modules.pi.models.volunteer import Volunteer
from app.modules.pi.repositories.volunteers import VolunteerRepository
from app.modules.pi.schemas.volunteers import (
    VolunteerCreateRequest,
    VolunteerUpdateRequest,
)


class VolunteerService:
    """Service for volunteer operations."""

    def __init__(self, repo: VolunteerRepository, audit: AuditPort):
        self.repo = repo
        self.audit = audit

    def _record(
        self,
        action: str,
        volunteer_id: int,
        actor: User,
        old_state: dict,
        new_state: dict,
    ) -> None:
        self.audit.record(
            AuditEntry(
                entity_type=EntityType.PI_VOLUNTEER.value,
                entity_id=str(volunteer_id),
                action=action,
                actor_id=str(actor.id),
                actor_display_name=actor.email,
                changes=calculate_delta(old_state, new_state),
            )
        )

    def _enrich_volunteer(self, volunteer: Volunteer) -> Volunteer:
        """Enrich volunteer with computed fields from database."""
        return self.repo.enrich(volunteer)

    def _sync_functions(self, volunteer_id: int, function_ids: list[int]) -> None:
        """Replace manually assigned functions for a volunteer."""
        try:
            self.repo.replace_functions(volunteer_id, function_ids)
        except ValueError as error:
            raise NotFoundError("One or more functions were not found") from error

    def get_volunteer_by_id(self, volunteer_id: int) -> Volunteer:
        """Get volunteer by ID or raise NotFoundError."""
        volunteer = self.repo.get_by_id(volunteer_id)
        if not volunteer:
            raise NotFoundError(f"Volunteer with ID {volunteer_id} not found")
        return self._enrich_volunteer(volunteer)

    def list_volunteers(
        self,
        skip: int = 0,
        limit: int = 100,
        full_name: str | None = None,
        email: str | None = None,
        status: str | None = None,
    ):
        """List volunteers with pagination and filters."""
        volunteers = self.repo.list_all(
            skip=skip, limit=limit, full_name=full_name, email=email, status=status
        )
        count = self.repo.count(full_name=full_name, email=email, status=status)

        # Enrich each volunteer with computed fields
        volunteers = [self._enrich_volunteer(v) for v in volunteers]
        return volunteers, count

    def create_volunteer(
        self, actor: User, request: VolunteerCreateRequest
    ) -> Volunteer:
        """Create new volunteer."""
        try:
            email = str(request.email)
            if self.repo.exists(email):
                raise ConflictError(f"Volunteer with email '{email}' already exists")

            volunteer = self.repo.create(request)
            self.repo.flush()
            self._sync_functions(volunteer.id, request.function_ids)
            self.repo.refresh(volunteer)
            volunteer = self._enrich_volunteer(volunteer)
            self._record(
                "CREATE", volunteer.id, actor, {}, volunteer_audit_state(volunteer)
            )
            self.repo.commit()
            return volunteer
        except Exception:
            self.repo.rollback()
            raise

    def update_volunteer(
        self,
        volunteer_id: int,
        actor: User,
        request: VolunteerUpdateRequest,
    ) -> Volunteer:
        """Update volunteer."""
        try:
            volunteer = self.get_volunteer_by_id(volunteer_id)
            old_state = volunteer_audit_state(volunteer)

            email = str(request.email) if request.email is not None else None
            if (
                "email" in request.model_fields_set
                and email is not None
                and email != volunteer.email
                and self.repo.exists(email)
            ):
                raise ConflictError(f"Volunteer with email '{email}' already exists")

            volunteer = self.repo.update(volunteer, request)
            self.repo.flush()
            if "function_ids" in request.model_fields_set:
                self._sync_functions(volunteer.id, request.function_ids or [])
            self.repo.refresh(volunteer)
            volunteer = self._enrich_volunteer(volunteer)
            new_state = volunteer_audit_state(volunteer)
            changes = calculate_delta(old_state, new_state)
            if not changes:
                # Genuine no-op: persist (nothing changed) without an audit entry.
                self.repo.commit(skip_audit=True)
                return volunteer
            self._record("UPDATE", volunteer.id, actor, old_state, new_state)
            self.repo.commit()
            return volunteer
        except Exception:
            self.repo.rollback()
            raise

    def delete_volunteer(self, volunteer_id: int, actor: User) -> None:
        """Delete volunteer."""
        try:
            volunteer = self.get_volunteer_by_id(volunteer_id)
            old_state = volunteer_audit_state(volunteer)
            self.repo.delete(volunteer)
            self._record("DELETE", volunteer.id, actor, old_state, {})
            self.repo.commit()
        except Exception:
            self.repo.rollback()
            raise
