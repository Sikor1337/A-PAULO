"""Group and assignment services for PI domain."""
from sqlalchemy.orm import Session

from app.core.errors import ConflictError, NotFoundError
from app.modules.pi.models.beneficiary import Beneficiary
from app.modules.pi.models.group import BeneficiaryAssignment, Group
from app.modules.pi.models.volunteer import Volunteer
from app.modules.pi.repositories.groups import (
    BeneficiaryAssignmentRepository,
    GroupRepository,
)


class GroupService:
    """Service for group operations."""

    def __init__(self, session: Session):
        self.session = session
        self.repo = GroupRepository(session)

    def get_group_by_id(self, group_id: int) -> Group:
        """Get group by ID or raise NotFoundError."""
        group = self.repo.get_by_id(group_id)
        if not group:
            raise NotFoundError(f"Group with ID {group_id} not found")
        return group

    def get_group_detail(self, group_id: int) -> dict:
        """Get group detail with leader name, beneficiaries and volunteers."""
        group = self.get_group_by_id(group_id)

        leader = None
        if group.leader_id:
            leader = (
                self.session.query(Volunteer)
                .filter(Volunteer.id == group.leader_id)
                .first()
            )

        beneficiaries = (
            self.session.query(Beneficiary)
            .filter(Beneficiary.group_id == group.id)
            .order_by(Beneficiary.full_name)
            .all()
        )

        beneficiary_ids = [b.id for b in beneficiaries]
        assignments_map: dict[int, list[dict]] = {b.id: [] for b in beneficiaries}

        if beneficiary_ids:
            rows = (
                self.session.query(BeneficiaryAssignment, Volunteer)
                .join(Volunteer, Volunteer.id == BeneficiaryAssignment.volunteer_id)
                .filter(BeneficiaryAssignment.beneficiary_id.in_(beneficiary_ids))
                .order_by(BeneficiaryAssignment.beneficiary_id, Volunteer.full_name)
                .all()
            )

            for assignment, volunteer in rows:
                assignments_map.setdefault(assignment.beneficiary_id, []).append(
                    {
                        "id": volunteer.id,
                        "full_name": volunteer.full_name,
                        "is_main": assignment.is_main,
                        "additional_info": assignment.additional_info or "",
                    }
                )

        return {
            "id": group.id,
            "name": group.name,
            "leader_id": group.leader_id,
            "leader_name": leader.full_name if leader else None,
            "beneficiaries": [
                {
                    "id": b.id,
                    "full_name": b.full_name,
                    "volunteers": assignments_map.get(b.id, []),
                }
                for b in beneficiaries
            ],
            "created_at": group.created_at,
            "updated_at": group.updated_at,
        }

    def list_groups(self, skip: int = 0, limit: int = 100, name: str = None):
        """List groups with pagination and filters."""
        groups = self.repo.list_all(skip=skip, limit=limit, name=name)
        count = self.repo.count(name=name)
        return groups, count

    def create_group(self, **kwargs) -> dict:
        """Create new group with optional assignments."""
        try:
            assignments = kwargs.pop("assignments", [])
            group = self.repo.create(**kwargs)
            self.session.flush()
            self.session.refresh(group)
            self._replace_group_assignments(group.id, assignments)
            self.session.commit()
            return self.get_group_detail(group.id)
        except Exception:
            self.session.rollback()
            raise

    def update_group(self, group_id: int, **kwargs) -> dict:
        """Update group with optional assignments."""
        try:
            assignments = kwargs.pop("assignments", None)
            group = self.get_group_by_id(group_id)
            updated_group = self.repo.update(group, **kwargs)
            self.session.flush()
            self.session.refresh(updated_group)

            if assignments is not None:
                self._replace_group_assignments(updated_group.id, assignments)

            self.session.commit()
            return self.get_group_detail(updated_group.id)
        except Exception:
            self.session.rollback()
            raise

    def delete_group(self, group_id: int) -> None:
        """Delete group."""
        try:
            group = self.get_group_by_id(group_id)
            self.repo.delete(group)
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise

    def _replace_group_assignments(self, group_id: int, assignments: list[dict]) -> None:
        """
        Replace full group assignments:
        - assign beneficiaries to the given group
        - remove beneficiaries removed from the group
        - replace beneficiary-volunteer assignments for affected beneficiaries
        """
        group = self.get_group_by_id(group_id)

        submitted_beneficiary_ids = {row["beneficiary"] for row in assignments}

        current_beneficiaries = (
            self.session.query(Beneficiary)
            .filter(Beneficiary.group_id == group.id)
            .all()
        )
        current_ids = {b.id for b in current_beneficiaries}

        # Beneficiaries removed from this group -> detach and delete assignments
        to_unassign = current_ids - submitted_beneficiary_ids
        if to_unassign:
            (
                self.session.query(Beneficiary)
                .filter(Beneficiary.id.in_(to_unassign))
                .update({"group_id": None}, synchronize_session=False)
            )
            (
                self.session.query(BeneficiaryAssignment)
                .filter(BeneficiaryAssignment.beneficiary_id.in_(to_unassign))
                .delete(synchronize_session=False)
            )

        # Insert / replace current rows
        for row in assignments:
            beneficiary_id = row["beneficiary"]
            volunteers = row.get("volunteers", [])
            main_volunteer = row.get("main_volunteer")

            beneficiary = (
                self.session.query(Beneficiary)
                .filter(Beneficiary.id == beneficiary_id)
                .first()
            )
            if not beneficiary:
                raise NotFoundError(f"Beneficiary with ID {beneficiary_id} not found")

            beneficiary.group_id = group.id

            # remove previous assignments for that beneficiary
            (
                self.session.query(BeneficiaryAssignment)
                .filter(BeneficiaryAssignment.beneficiary_id == beneficiary_id)
                .delete(synchronize_session=False)
            )

            for volunteer_row in volunteers:
                volunteer_id = volunteer_row["id"]
                additional_info = volunteer_row.get("additional_info", "")

                volunteer = (
                    self.session.query(Volunteer)
                    .filter(Volunteer.id == volunteer_id)
                    .first()
                )
                if not volunteer:
                    raise NotFoundError(f"Volunteer with ID {volunteer_id} not found")

                assignment = BeneficiaryAssignment(
                    beneficiary_id=beneficiary_id,
                    volunteer_id=volunteer_id,
                    is_main=(main_volunteer == volunteer_id),
                    additional_info=additional_info,
                )
                self.session.add(assignment)


class BeneficiaryAssignmentService:
    """Service for beneficiary assignment operations."""

    def __init__(self, session: Session):
        self.session = session
        self.repo = BeneficiaryAssignmentRepository(session)

    def get_assignment_by_id(self, assignment_id: int) -> BeneficiaryAssignment:
        """Get assignment by ID or raise NotFoundError."""
        assignment = self.repo.get_by_id(assignment_id)
        if not assignment:
            raise NotFoundError(f"Assignment with ID {assignment_id} not found")
        return assignment

    def list_assignments(self, skip: int = 0, limit: int = 100):
        """List assignments with pagination."""
        assignments = self.repo.list_all(skip=skip, limit=limit)
        return assignments

    def create_assignment(
        self, beneficiary_id: int, volunteer_id: int, **kwargs
    ) -> BeneficiaryAssignment:
        """Create new assignment."""
        try:
            existing = self.repo.get_by_beneficiary_volunteer(beneficiary_id, volunteer_id)
            if existing:
                raise ConflictError(
                    f"Assignment for beneficiary {beneficiary_id} and volunteer {volunteer_id} already exists"
                )

            assignment = self.repo.create(
                beneficiary_id=beneficiary_id,
                volunteer_id=volunteer_id,
                **kwargs,
            )
            self.session.flush()
            self.session.refresh(assignment)
            self.session.commit()
            return assignment
        except Exception:
            self.session.rollback()
            raise

    def update_assignment(self, assignment_id: int, **kwargs) -> BeneficiaryAssignment:
        """Update assignment."""
        try:
            assignment = self.get_assignment_by_id(assignment_id)
            assignment = self.repo.update(assignment, **kwargs)
            self.session.flush()
            self.session.refresh(assignment)
            self.session.commit()
            return assignment
        except Exception:
            self.session.rollback()
            raise

    def delete_assignment(self, assignment_id: int) -> None:
        """Delete assignment."""
        try:
            assignment = self.get_assignment_by_id(assignment_id)
            self.repo.delete(assignment)
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise