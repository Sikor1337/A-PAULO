"""Group and assignment services for PI domain."""

from app.core.audit import AuditEntry, AuditPort, EntityType, calculate_delta
from app.core.errors import ConflictError, NotFoundError
from app.modules.core_data.models import User
from app.modules.pi.audit_state import (
    assignment_audit_state,
    beneficiary_audit_state,
    group_audit_state,
)
from app.modules.pi.models.group import BeneficiaryAssignment, Group
from app.modules.pi.repositories.groups import (
    BeneficiaryAssignmentRepository,
    GroupRepository,
)


class GroupService:
    """Service for group operations."""

    def __init__(self, repo: GroupRepository, audit: AuditPort):
        self.repo = repo
        self.audit = audit

    def _record(
        self,
        action: str,
        group_id: int,
        actor: User,
        old_state: dict,
        new_state: dict,
    ) -> None:
        self.audit.record(
            AuditEntry(
                entity_type=EntityType.PI_GROUP.value,
                entity_id=str(group_id),
                action=action,
                actor_id=str(actor.id),
                actor_display_name=actor.email,
                changes=calculate_delta(old_state, new_state),
            )
        )

    def _capture_beneficiaries(self, beneficiary_ids: set[int]) -> dict[int, dict]:
        states = {}
        for beneficiary_id in beneficiary_ids:
            beneficiary = self.repo.get_beneficiary(beneficiary_id)
            if beneficiary:
                states[beneficiary_id] = beneficiary_audit_state(beneficiary)
        return states

    def _record_beneficiary_changes(
        self,
        before: dict[int, dict],
        group_id: int,
        actor: User,
    ) -> None:
        for beneficiary_id, old_state in before.items():
            beneficiary = self.repo.get_beneficiary(beneficiary_id)
            if not beneficiary:
                continue
            new_state = beneficiary_audit_state(beneficiary)
            changes = calculate_delta(old_state, new_state)
            if not changes:
                continue
            self.audit.record(
                AuditEntry(
                    entity_type=EntityType.PI_BENEFICIARY.value,
                    entity_id=str(beneficiary_id),
                    action="GROUP_ASSIGNMENT_UPDATE",
                    actor_id=str(actor.id),
                    actor_display_name=actor.email,
                    changes=changes,
                    context_type=EntityType.PI_GROUP.value,
                    context_id=str(group_id),
                )
            )

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

    def create_group(self, actor: User, **kwargs) -> dict:
        """Create new group with optional assignments."""
        try:
            assignments = kwargs.pop("assignments", [])
            beneficiary_states = self._capture_beneficiaries(
                {row["beneficiary"] for row in assignments}
            )
            group = self.repo.create(**kwargs)
            self.repo.flush()
            self.repo.refresh(group)
            self._replace_group_assignments(group.id, assignments)
            self.repo.flush()
            detail = self.get_group_detail(group.id)
            self._record_beneficiary_changes(beneficiary_states, group.id, actor)
            self._record("CREATE", group.id, actor, {}, group_audit_state(group))
            self.repo.commit()
            return detail
        except Exception:
            self.repo.rollback()
            raise

    def update_group(self, group_id: int, actor: User, **kwargs) -> dict:
        """Update group with optional assignments."""
        try:
            assignments = kwargs.pop("assignments", None)
            group = self.get_group_by_id(group_id)
            old_detail = self.get_group_detail(group_id)
            old_state = group_audit_state(group)
            affected_beneficiary_ids = {
                item["id"] for item in old_detail.get("beneficiaries", [])
            }
            if assignments is not None:
                affected_beneficiary_ids.update(
                    row["beneficiary"] for row in assignments
                )
            beneficiary_states = self._capture_beneficiaries(affected_beneficiary_ids)
            updated_group = self.repo.update(group, **kwargs)
            self.repo.flush()
            self.repo.refresh(updated_group)

            if assignments is not None:
                self._replace_group_assignments(updated_group.id, assignments)

            self.repo.flush()
            detail = self.get_group_detail(updated_group.id)
            new_state = group_audit_state(updated_group)
            changes = calculate_delta(old_state, new_state)
            if not changes:
                self.repo.rollback()
                return self.get_group_detail(group_id)
            self._record("UPDATE", group.id, actor, old_state, new_state)
            self._record_beneficiary_changes(beneficiary_states, group.id, actor)
            self.repo.commit()
            return detail
        except Exception:
            self.repo.rollback()
            raise

    def delete_group(self, group_id: int, actor: User) -> None:
        """Delete group."""
        try:
            group = self.get_group_by_id(group_id)
            old_state = group_audit_state(self.get_group_detail(group_id))
            beneficiary_states = self._capture_beneficiaries(
                {item["beneficiary_id"] for item in old_state["assignments"]}
            )
            self.repo.delete(group)
            self.repo.flush()
            self._record("DELETE", group.id, actor, old_state, {})
            self._record_beneficiary_changes(beneficiary_states, group.id, actor)
            self.repo.commit()
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

    def __init__(self, repo: BeneficiaryAssignmentRepository, audit: AuditPort):
        self.repo = repo
        self.audit = audit

    def _record(
        self,
        action: str,
        assignment: BeneficiaryAssignment,
        actor: User,
        old_state: dict,
        new_state: dict,
    ) -> None:
        group_id = self.repo.group_id_for_beneficiary(assignment.beneficiary_id)
        self.audit.record(
            AuditEntry(
                entity_type=EntityType.PI_BENEFICIARY_ASSIGNMENT.value,
                entity_id=str(assignment.id),
                action=action,
                actor_id=str(actor.id),
                actor_display_name=actor.email,
                changes=calculate_delta(old_state, new_state),
                context_type=(EntityType.PI_GROUP.value if group_id else None),
                context_id=str(group_id) if group_id else None,
            )
        )

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
        self, beneficiary_id: int, volunteer_id: int, actor: User, **kwargs
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
            self._record(
                "ASSIGNMENT_CREATE",
                assignment,
                actor,
                {},
                assignment_audit_state(assignment),
            )
            self.repo.commit()
            return assignment
        except Exception:
            self.repo.rollback()
            raise

    def update_assignment(
        self, assignment_id: int, actor: User, **kwargs
    ) -> BeneficiaryAssignment:
        """Update assignment."""
        try:
            assignment = self.get_assignment_by_id(assignment_id)
            old_state = assignment_audit_state(assignment)
            assignment = self.repo.update(assignment, **kwargs)
            self.repo.flush()
            self.repo.refresh(assignment)
            new_state = assignment_audit_state(assignment)
            changes = calculate_delta(old_state, new_state)
            if not changes:
                self.repo.rollback()
                return self.get_assignment_by_id(assignment_id)
            self._record("ASSIGNMENT_UPDATE", assignment, actor, old_state, new_state)
            self.repo.commit()
            return assignment
        except Exception:
            self.repo.rollback()
            raise

    def delete_assignment(self, assignment_id: int, actor: User) -> None:
        """Delete assignment."""
        try:
            assignment = self.get_assignment_by_id(assignment_id)
            old_state = assignment_audit_state(assignment)
            self._record("ASSIGNMENT_DELETE", assignment, actor, old_state, {})
            self.repo.delete(assignment)
            self.repo.commit()
        except Exception:
            self.repo.rollback()
            raise
