"""Group and assignment repositories for PI domain."""

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.infrastructure.sql.repository import SQLRepository
from app.modules.pi.models.beneficiary import Beneficiary
from app.modules.pi.models.group import BeneficiaryAssignment, Group
from app.modules.pi.models.volunteer import Volunteer


class GroupRepository(SQLRepository):
    """Repository for Group model database operations."""

    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, group_id: int) -> Group | None:
        """Get group by ID."""
        return self.session.query(Group).filter(Group.id == group_id).first()

    def list_all(
        self, skip: int = 0, limit: int = 100, name: str | None = None
    ) -> list[Group]:
        """List groups with optional filters."""
        query = self.session.query(Group)

        if name:
            query = query.filter(Group.name.ilike(f"%{name}%"))

        return query.order_by(Group.name).offset(skip).limit(limit).all()

    def count(self, name: str | None = None) -> int:
        """Count groups with optional filters."""
        query = self.session.query(func.count(Group.id))

        if name:
            query = query.filter(Group.name.ilike(f"%{name}%"))

        return query.scalar() or 0

    def create(self, **kwargs) -> Group:
        """Create new group."""
        group = Group(**kwargs)
        self.session.add(group)
        return group

    def update(self, group: Group, **kwargs) -> Group:
        """Update group."""
        for key, value in kwargs.items():
            if hasattr(group, key):
                setattr(group, key, value)
        return group

    def delete(self, group: Group) -> None:
        """Delete group."""
        self.session.delete(group)

    def detail(self, group: Group) -> dict:
        leader = (
            self.session.query(Volunteer)
            .filter(Volunteer.id == group.leader_id)
            .first()
            if group.leader_id
            else None
        )
        beneficiaries = (
            self.session.query(Beneficiary)
            .filter(Beneficiary.group_id == group.id)
            .order_by(Beneficiary.full_name)
            .all()
        )
        assignments: dict[int, list[dict]] = {item.id: [] for item in beneficiaries}
        beneficiary_ids = [item.id for item in beneficiaries]
        if beneficiary_ids:
            rows = (
                self.session.query(BeneficiaryAssignment, Volunteer)
                .join(Volunteer, Volunteer.id == BeneficiaryAssignment.volunteer_id)
                .filter(BeneficiaryAssignment.beneficiary_id.in_(beneficiary_ids))
                .order_by(BeneficiaryAssignment.beneficiary_id, Volunteer.full_name)
                .all()
            )
            for assignment, volunteer in rows:
                assignments[assignment.beneficiary_id].append(
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
                    "id": item.id,
                    "full_name": item.full_name,
                    "volunteers": assignments[item.id],
                }
                for item in beneficiaries
            ],
            "created_at": group.created_at,
            "updated_at": group.updated_at,
        }

    def replace_assignments(self, group: Group, rows: list[dict]) -> None:
        submitted_ids = {row["beneficiary"] for row in rows}
        current_ids = {
            item.id
            for item in self.session.query(Beneficiary)
            .filter(Beneficiary.group_id == group.id)
            .all()
        }
        removed_ids = current_ids - submitted_ids
        if removed_ids:
            self.session.query(Beneficiary).filter(
                Beneficiary.id.in_(removed_ids)
            ).update({"group_id": None}, synchronize_session=False)
            self.session.query(BeneficiaryAssignment).filter(
                BeneficiaryAssignment.beneficiary_id.in_(removed_ids)
            ).delete(synchronize_session=False)

        for row in rows:
            beneficiary_id = row["beneficiary"]
            beneficiary = self.session.get(Beneficiary, beneficiary_id)
            if beneficiary is None:
                raise LookupError(f"beneficiary:{beneficiary_id}")
            beneficiary.group_id = group.id
            self.session.query(BeneficiaryAssignment).filter(
                BeneficiaryAssignment.beneficiary_id == beneficiary_id
            ).delete(synchronize_session=False)
            main_volunteer = row.get("main_volunteer")
            for volunteer_row in row.get("volunteers", []):
                volunteer_id = volunteer_row["id"]
                if self.session.get(Volunteer, volunteer_id) is None:
                    raise LookupError(f"volunteer:{volunteer_id}")
                self.session.add(
                    BeneficiaryAssignment(
                        beneficiary_id=beneficiary_id,
                        volunteer_id=volunteer_id,
                        is_main=main_volunteer == volunteer_id,
                        additional_info=volunteer_row.get("additional_info", ""),
                    )
                )


class BeneficiaryAssignmentRepository(SQLRepository):
    """Repository for BeneficiaryAssignment model database operations."""

    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, assignment_id: int) -> BeneficiaryAssignment | None:
        """Get assignment by ID."""
        return (
            self.session.query(BeneficiaryAssignment)
            .filter(BeneficiaryAssignment.id == assignment_id)
            .first()
        )

    def get_by_beneficiary_volunteer(
        self, beneficiary_id: int, volunteer_id: int
    ) -> BeneficiaryAssignment | None:
        """Get assignment by beneficiary and volunteer IDs."""
        return (
            self.session.query(BeneficiaryAssignment)
            .filter(
                BeneficiaryAssignment.beneficiary_id == beneficiary_id,
                BeneficiaryAssignment.volunteer_id == volunteer_id,
            )
            .first()
        )

    def list_all(self, skip: int = 0, limit: int = 100) -> list[BeneficiaryAssignment]:
        """List all assignments."""
        return (
            self.session.query(BeneficiaryAssignment)
            .order_by(BeneficiaryAssignment.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create(self, **kwargs) -> BeneficiaryAssignment:
        """Create new assignment."""
        assignment = BeneficiaryAssignment(**kwargs)
        self.session.add(assignment)
        return assignment

    def update(
        self, assignment: BeneficiaryAssignment, **kwargs
    ) -> BeneficiaryAssignment:
        """Update assignment."""
        for key, value in kwargs.items():
            if hasattr(assignment, key):
                setattr(assignment, key, value)
        return assignment

    def delete(self, assignment: BeneficiaryAssignment) -> None:
        self.session.delete(assignment)
