"""Volunteer service for PI domain."""

from app.core.audit import AuditEntry, AuditPort, EntityType, calculate_delta
from app.core.errors import ConflictError, NotFoundError
from app.modules.core_data.models import User
from app.modules.pi.audit_state import volunteer_audit_state
from app.modules.pi.models.volunteer import Volunteer
from app.modules.pi.repositories.volunteers import VolunteerRepository


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

    def create_volunteer(self, actor: User, **kwargs) -> Volunteer:
        """Create new volunteer."""
        try:
            function_ids = kwargs.pop("function_ids", [])
            # Check if email already exists
            if self.repo.exists(kwargs.get("email")):
                raise ConflictError(
                    f"Volunteer with email '{kwargs.get('email')}' already exists"
                )

            volunteer = self.repo.create(**kwargs)
            self.repo.flush()
            self._sync_functions(volunteer.id, function_ids)
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

    def update_volunteer(self, volunteer_id: int, actor: User, **kwargs) -> Volunteer:
        """Update volunteer."""
        try:
            function_ids = kwargs.pop("function_ids", None)
            volunteer = self.get_volunteer_by_id(volunteer_id)
            old_state = volunteer_audit_state(volunteer)

            # If email is being updated, check uniqueness (excluding current volunteer)
            if (
                "email" in kwargs
                and kwargs["email"] != volunteer.email
                and self.repo.exists(kwargs["email"])
            ):
                raise ConflictError(
                    f"Volunteer with email '{kwargs['email']}' already exists"
                )

            volunteer = self.repo.update(volunteer, **kwargs)
            self.repo.flush()
            if function_ids is not None:
                self._sync_functions(volunteer.id, function_ids)
            self.repo.refresh(volunteer)
            volunteer = self._enrich_volunteer(volunteer)
            new_state = volunteer_audit_state(volunteer)
            changes = calculate_delta(old_state, new_state)
            if not changes:
                self.repo.rollback()
                return self.get_volunteer_by_id(volunteer_id)
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
