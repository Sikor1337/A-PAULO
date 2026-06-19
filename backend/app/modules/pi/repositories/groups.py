"""Group and assignment repositories for PI domain."""
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.modules.pi.models.group import Group, BeneficiaryAssignment


class GroupRepository:
    """Repository for Group model database operations."""

    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, group_id: int) -> Group | None:
        """Get group by ID."""
        return self.session.query(Group).filter(Group.id == group_id).first()

    def list_all(self, skip: int = 0, limit: int = 100, name: str = None) -> list[Group]:
        """List groups with optional filters."""
        query = self.session.query(Group)

        if name:
            query = query.filter(Group.name.ilike(f"%{name}%"))

        return query.order_by(Group.name).offset(skip).limit(limit).all()

    def count(self, name: str = None) -> int:
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


class BeneficiaryAssignmentRepository:
    """Repository for BeneficiaryAssignment model database operations."""

    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, assignment_id: int) -> BeneficiaryAssignment | None:
        """Get assignment by ID."""
        return self.session.query(BeneficiaryAssignment).filter(
            BeneficiaryAssignment.id == assignment_id
        ).first()

    def get_by_beneficiary_volunteer(
        self, beneficiary_id: int, volunteer_id: int
    ) -> BeneficiaryAssignment | None:
        """Get assignment by beneficiary and volunteer IDs."""
        return self.session.query(BeneficiaryAssignment).filter(
            BeneficiaryAssignment.beneficiary_id == beneficiary_id,
            BeneficiaryAssignment.volunteer_id == volunteer_id,
        ).first()

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

    def update(self, assignment: BeneficiaryAssignment, **kwargs) -> BeneficiaryAssignment:
        """Update assignment."""
        for key, value in kwargs.items():
            if hasattr(assignment, key):
                setattr(assignment, key, value)
        try:
            self.session.commit()
            self.session.refresh(assignment)
            return assignment
        except Exception:
            self.session.rollback()
            raise
