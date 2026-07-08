"""Department repository."""

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.infrastructure.sql.repository import SQLRepository
from app.modules.departments.models.departments import Department, DepartmentMember
from app.modules.pi.models.volunteer import Volunteer


class DepartmentRepository(SQLRepository):
    """Data access for departments and their members."""

    def __init__(self, session: Session):
        self.session = session

    def list_all(self, include_archived: bool = False) -> list[Department]:
        query = self.session.query(Department)
        if not include_archived:
            query = query.filter(Department.is_archived.is_(False))
        return query.order_by(Department.name).all()

    def get_by_id(self, department_id: int) -> Department | None:
        return (
            self.session.query(Department)
            .filter(Department.id == department_id)
            .first()
        )

    def get_by_name(self, name: str) -> Department | None:
        return (
            self.session.query(Department)
            .filter(func.lower(Department.name) == name.lower())
            .first()
        )

    def create(self, **kwargs) -> Department:
        department = Department(**kwargs)
        self.session.add(department)
        return department

    def update(self, department: Department, **kwargs) -> Department:
        for key, value in kwargs.items():
            if hasattr(department, key):
                setattr(department, key, value)
        return department

    def member_counts(self) -> dict[int, int]:
        """Member count per department id."""
        rows = (
            self.session.query(
                DepartmentMember.department_id, func.count(DepartmentMember.id)
            )
            .group_by(DepartmentMember.department_id)
            .all()
        )
        return dict(rows)

    def list_members(
        self, department_id: int
    ) -> list[tuple[DepartmentMember, Volunteer]]:
        return (
            self.session.query(DepartmentMember, Volunteer)
            .join(Volunteer, Volunteer.id == DepartmentMember.volunteer_id)
            .filter(DepartmentMember.department_id == department_id)
            .order_by(Volunteer.full_name)
            .all()
        )

    def get_member(
        self, department_id: int, volunteer_id: int
    ) -> DepartmentMember | None:
        return (
            self.session.query(DepartmentMember)
            .filter(
                DepartmentMember.department_id == department_id,
                DepartmentMember.volunteer_id == volunteer_id,
            )
            .first()
        )

    def add_member(self, department_id: int, volunteer_id: int) -> DepartmentMember:
        member = DepartmentMember(
            department_id=department_id, volunteer_id=volunteer_id
        )
        self.session.add(member)
        return member

    def remove_member(self, member: DepartmentMember) -> None:
        self.session.delete(member)

    def volunteer_exists(self, volunteer_id: int) -> bool:
        return (
            self.session.query(Volunteer.id)
            .filter(Volunteer.id == volunteer_id)
            .first()
            is not None
        )
