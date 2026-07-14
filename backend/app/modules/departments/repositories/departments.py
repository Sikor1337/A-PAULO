"""Department repository."""

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.infrastructure.sql.repository import SQLRepository
from app.modules.departments.models.departments import (
    Department,
    DepartmentInventoryItem,
    DepartmentMember,
    MembershipStatus,
)
from app.modules.departments.schemas.departments import (
    DepartmentCreateRequest,
    DepartmentInventoryItemInput,
    DepartmentUpdateRequest,
)
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

    def create(self, request: DepartmentCreateRequest) -> Department:
        department = Department(
            name=request.name,
            icon=request.icon,
            description=request.description,
        )
        self.session.add(department)
        return department

    def update(
        self, department: Department, request: DepartmentUpdateRequest
    ) -> Department:
        if request.name is not None:
            department.name = request.name
        if request.icon is not None:
            department.icon = request.icon
        if request.description is not None:
            department.description = request.description
        if request.is_archived is not None:
            department.is_archived = request.is_archived
        return department

    def member_counts(self) -> dict[int, int]:
        """Active member count per department id (pending requests excluded)."""
        rows = (
            self.session.query(
                DepartmentMember.department_id, func.count(DepartmentMember.id)
            )
            .filter(DepartmentMember.status == MembershipStatus.ACTIVE.value)
            .group_by(DepartmentMember.department_id)
            .all()
        )
        return {department_id: count for department_id, count in rows}

    def list_members(
        self, department_id: int
    ) -> list[tuple[DepartmentMember, Volunteer]]:
        rows = (
            self.session.query(DepartmentMember, Volunteer)
            .join(Volunteer, Volunteer.id == DepartmentMember.volunteer_id)
            .filter(DepartmentMember.department_id == department_id)
            .order_by(Volunteer.full_name)
            .all()
        )
        return [(member, volunteer) for member, volunteer in rows]

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

    def add_member(
        self,
        department_id: int,
        volunteer_id: int,
        status: str = MembershipStatus.ACTIVE.value,
    ) -> DepartmentMember:
        member = DepartmentMember(
            department_id=department_id,
            volunteer_id=volunteer_id,
            status=status,
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

    def get_volunteer_by_email(self, email: str) -> Volunteer | None:
        return (
            self.session.query(Volunteer)
            .filter(func.lower(Volunteer.email) == email.lower())
            .first()
        )

    def list_inventory(self, department_id: int) -> list[DepartmentInventoryItem]:
        return (
            self.session.query(DepartmentInventoryItem)
            .filter(DepartmentInventoryItem.department_id == department_id)
            .order_by(DepartmentInventoryItem.name, DepartmentInventoryItem.id)
            .all()
        )

    def get_inventory_item(
        self, department_id: int, item_id: int
    ) -> DepartmentInventoryItem | None:
        return (
            self.session.query(DepartmentInventoryItem)
            .filter(
                DepartmentInventoryItem.department_id == department_id,
                DepartmentInventoryItem.id == item_id,
            )
            .first()
        )

    def create_inventory_item(
        self, department_id: int, request: DepartmentInventoryItemInput
    ) -> DepartmentInventoryItem:
        item = DepartmentInventoryItem(
            department_id=department_id,
            name=request.name,
            location=request.location,
            borrowed_by_volunteer_id=request.borrowed_by_volunteer_id,
            borrowed_by_volunteer=(
                self.session.get(Volunteer, request.borrowed_by_volunteer_id)
                if request.borrowed_by_volunteer_id is not None
                else None
            ),
            borrowed_at=request.borrowed_at,
        )
        self.session.add(item)
        return item

    def update_inventory_item(
        self,
        item: DepartmentInventoryItem,
        request: DepartmentInventoryItemInput,
    ) -> DepartmentInventoryItem:
        item.name = request.name
        item.location = request.location
        item.borrowed_by_volunteer_id = request.borrowed_by_volunteer_id
        item.borrowed_by_volunteer = (
            self.session.get(Volunteer, request.borrowed_by_volunteer_id)
            if request.borrowed_by_volunteer_id is not None
            else None
        )
        item.borrowed_at = request.borrowed_at
        return item

    def delete_inventory_item(self, item: DepartmentInventoryItem) -> None:
        self.session.delete(item)
