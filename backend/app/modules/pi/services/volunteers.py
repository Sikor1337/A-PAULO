"""Volunteer service for PI domain."""

from app.core.errors import ConflictError, NotFoundError
from app.modules.pi.models.volunteer import Volunteer
from app.modules.pi.repositories.volunteers import VolunteerRepository


class VolunteerService:
    """Service for volunteer operations."""

    def __init__(self, repo: VolunteerRepository):
        self.repo = repo

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

    def create_volunteer(self, **kwargs) -> Volunteer:
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
            self.repo.commit(skip_audit=True)
            return self._enrich_volunteer(volunteer)
        except Exception:
            self.repo.rollback()
            raise

    def update_volunteer(self, volunteer_id: int, **kwargs) -> Volunteer:
        """Update volunteer."""
        try:
            function_ids = kwargs.pop("function_ids", None)
            volunteer = self.get_volunteer_by_id(volunteer_id)

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
            self.repo.commit(skip_audit=True)
            return self._enrich_volunteer(volunteer)
        except Exception:
            self.repo.rollback()
            raise

    def delete_volunteer(self, volunteer_id: int) -> None:
        """Delete volunteer."""
        try:
            volunteer = self.get_volunteer_by_id(volunteer_id)
            self.repo.delete(volunteer)
            self.repo.commit(skip_audit=True)
        except Exception:
            self.repo.rollback()
            raise
