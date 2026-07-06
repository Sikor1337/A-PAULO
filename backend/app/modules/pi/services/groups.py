"""Group and assignment services for PI domain."""

from app.core.errors import ConflictError, NotFoundError
from app.modules.pi.models.group import BeneficiaryAssignment, Group
from app.modules.pi.repositories.groups import (
    BeneficiaryAssignmentRepository,
    GroupRepository,
)


class GroupService:
    """Service for group operations."""

    def __init__(self, repo: GroupRepository):
        self.repo = repo

    def get_group_by_id(self, group_id: int) -> Group:
        """Get group by ID or raise NotFoundError."""
        group = self.repo.get_by_id(group_id)
        if not group:
            raise NotFoundError(f"Group with ID {group_id} not found")
        return group

    def get_group_detail(self, group_id: int) -> dict:
        """Get group detail with leader name, beneficiaries and volunteers."""
        group = self.get_group_by_id(group_id)

        return self.repo.detail(group)

    def list_groups(self, skip: int = 0, limit: int = 100, name: str | None = None):
        """List groups with pagination and filters."""
        groups = self.repo.list_all(skip=skip, limit=limit, name=name)
        count = self.repo.count(name=name)
        return groups, count

    def create_group(self, **kwargs) -> dict:
        """Create new group with optional assignments."""
        try:
            assignments = kwargs.pop("assignments", [])
            group = self.repo.create(**kwargs)
            self.repo.flush()
            self.repo.refresh(group)
            self._replace_group_assignments(group.id, assignments)
            self.repo.commit(skip_audit=True)
            return self.get_group_detail(group.id)
        except Exception:
            self.repo.rollback()
            raise

    def update_group(self, group_id: int, **kwargs) -> dict:
        """Update group with optional assignments."""
        try:
            assignments = kwargs.pop("assignments", None)
            group = self.get_group_by_id(group_id)
            updated_group = self.repo.update(group, **kwargs)
            self.repo.flush()
            self.repo.refresh(updated_group)

            if assignments is not None:
                self._replace_group_assignments(updated_group.id, assignments)

            self.repo.commit(skip_audit=True)
            return self.get_group_detail(updated_group.id)
        except Exception:
            self.repo.rollback()
            raise

    def delete_group(self, group_id: int) -> None:
        """Delete group."""
        try:
            group = self.get_group_by_id(group_id)
            self.repo.delete(group)
            self.repo.commit(skip_audit=True)
        except Exception:
            self.repo.rollback()
            raise

    def _replace_group_assignments(
        self, group_id: int, assignments: list[dict]
    ) -> None:
        """
        Replace full group assignments:
        - assign beneficiaries to the given group
        - remove beneficiaries removed from the group
        - replace beneficiary-volunteer assignments for affected beneficiaries
        """
        group = self.get_group_by_id(group_id)
        try:
            self.repo.replace_assignments(group, assignments)
        except LookupError as error:
            entity, entity_id = str(error).split(":", 1)
            raise NotFoundError(
                f"{entity.title()} with ID {entity_id} not found"
            ) from error


class BeneficiaryAssignmentService:
    """Service for beneficiary assignment operations."""

    def __init__(self, repo: BeneficiaryAssignmentRepository):
        self.repo = repo

    def get_assignment_by_id(self, assignment_id: int) -> BeneficiaryAssignment:
        """Get assignment by ID or raise NotFoundError."""
        assignment = self.repo.get_by_id(assignment_id)
        if not assignment:
            raise NotFoundError(f"Assignment with ID {assignment_id} not found")
        return assignment

    def list_assignments(self, skip: int = 0, limit: int = 100):
        """List assignments with pagination."""
        return self.repo.list_all(skip=skip, limit=limit)

    def create_assignment(
        self, beneficiary_id: int, volunteer_id: int, **kwargs
    ) -> BeneficiaryAssignment:
        """Create new assignment."""
        try:
            existing = self.repo.get_by_beneficiary_volunteer(
                beneficiary_id, volunteer_id
            )
            if existing:
                raise ConflictError(
                    "Assignment for beneficiary "
                    f"{beneficiary_id} and volunteer {volunteer_id} already exists"
                )

            assignment = self.repo.create(
                beneficiary_id=beneficiary_id,
                volunteer_id=volunteer_id,
                **kwargs,
            )
            self.repo.flush()
            self.repo.refresh(assignment)
            self.repo.commit(skip_audit=True)
            return assignment
        except Exception:
            self.repo.rollback()
            raise

    def update_assignment(self, assignment_id: int, **kwargs) -> BeneficiaryAssignment:
        """Update assignment."""
        try:
            assignment = self.get_assignment_by_id(assignment_id)
            assignment = self.repo.update(assignment, **kwargs)
            self.repo.flush()
            self.repo.refresh(assignment)
            self.repo.commit(skip_audit=True)
            return assignment
        except Exception:
            self.repo.rollback()
            raise

    def delete_assignment(self, assignment_id: int) -> None:
        """Delete assignment."""
        try:
            assignment = self.get_assignment_by_id(assignment_id)
            self.repo.delete(assignment)
            self.repo.commit(skip_audit=True)
        except Exception:
            self.repo.rollback()
            raise
