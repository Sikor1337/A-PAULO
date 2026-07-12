"""Department business logic."""

from app.core.errors import ConflictError, NotFoundError, ValidationException
from app.modules.core_data.models import User
from app.modules.departments.models.departments import (
    Department,
    DepartmentInventoryItem,
    MembershipStatus,
)
from app.modules.departments.repositories.departments import DepartmentRepository
from app.modules.pi.models.volunteer import Volunteer


class DepartmentService:
    """Departments: archive instead of delete, unique names, member roster."""

    def __init__(self, repo: DepartmentRepository):
        self.repo = repo

    def get_department(self, department_id: int) -> Department:
        department = self.repo.get_by_id(department_id)
        if not department:
            raise NotFoundError("Dział nie istnieje")
        return department

    def list_departments(self, include_archived: bool = False) -> list[dict]:
        counts = self.repo.member_counts()
        return [
            self._serialize_list_item(department, counts.get(department.id, 0))
            for department in self.repo.list_all(include_archived=include_archived)
        ]

    def get_department_detail(self, department_id: int) -> dict:
        department = self.get_department(department_id)
        return self._serialize_detail(department)

    def create_department(
        self, *, name: str, icon: str = "", description: str = ""
    ) -> dict:
        try:
            if self.repo.get_by_name(name):
                raise ConflictError("Dział o tej nazwie już istnieje")
            department = self.repo.create(
                name=name, icon=icon, description=description
            )
            self.repo.flush()
            self.repo.refresh(department)
            self.repo.commit(skip_audit=True)
            return self._serialize_detail(department)
        except Exception:
            self.repo.rollback()
            raise

    def update_department(self, department_id: int, **kwargs) -> dict:
        try:
            department = self.get_department(department_id)
            new_name = kwargs.get("name")
            if new_name and new_name.lower() != department.name.lower():
                duplicate = self.repo.get_by_name(new_name)
                if duplicate and duplicate.id != department.id:
                    raise ConflictError("Dział o tej nazwie już istnieje")
            department = self.repo.update(department, **kwargs)
            self.repo.flush()
            self.repo.refresh(department)
            self.repo.commit(skip_audit=True)
            return self._serialize_detail(department)
        except Exception:
            self.repo.rollback()
            raise

    def add_member(self, department_id: int, volunteer_id: int) -> dict:
        try:
            department = self.get_department(department_id)
            if department.is_archived:
                raise ValidationException(
                    "Nie można dodawać członków do zarchiwizowanego działu"
                )
            if not self.repo.volunteer_exists(volunteer_id):
                raise NotFoundError("Wolontariusz nie istnieje")
            if self.repo.get_member(department_id, volunteer_id):
                raise ConflictError("Wolontariusz już należy do tego działu")
            # A manager-added member is active immediately.
            self.repo.add_member(
                department_id, volunteer_id, status=MembershipStatus.ACTIVE.value
            )
            self.repo.commit(skip_audit=True)
            return self._serialize_detail(department)
        except Exception:
            self.repo.rollback()
            raise

    def request_membership(self, department_id: int, user: User) -> dict:
        """A volunteer asks to join; the request awaits approval (PAP-91)."""
        try:
            department = self.get_department(department_id)
            if department.is_archived:
                raise ValidationException(
                    "Nie można dołączyć do zarchiwizowanego działu"
                )
            volunteer = self._volunteer_for_user(user)
            if self.repo.get_member(department_id, volunteer.id):
                raise ConflictError(
                    "Masz już członkostwo lub oczekującą prośbę w tym dziale"
                )
            self.repo.add_member(
                department_id, volunteer.id, status=MembershipStatus.PENDING.value
            )
            self.repo.commit(skip_audit=True)
            return self._serialize_detail(department)
        except Exception:
            self.repo.rollback()
            raise

    def approve_member(self, department_id: int, volunteer_id: int) -> dict:
        """Approve a pending join request, turning it into full membership."""
        try:
            department = self.get_department(department_id)
            member = self.repo.get_member(department_id, volunteer_id)
            if not member:
                raise NotFoundError("Brak prośby o dołączenie do tego działu")
            if member.status == MembershipStatus.ACTIVE.value:
                raise ConflictError("Wolontariusz jest już aktywnym członkiem")
            member.status = MembershipStatus.ACTIVE.value
            self.repo.commit(skip_audit=True)
            return self._serialize_detail(department)
        except Exception:
            self.repo.rollback()
            raise

    def leave_department(self, department_id: int, user: User) -> dict:
        """Remove the current volunteer's own membership (PAP-91)."""
        try:
            department = self.get_department(department_id)
            volunteer = self._volunteer_for_user(user)
            member = self.repo.get_member(department_id, volunteer.id)
            if not member:
                raise NotFoundError("Nie należysz do tego działu")
            self.repo.remove_member(member)
            self.repo.commit(skip_audit=True)
            return self._serialize_detail(department)
        except Exception:
            self.repo.rollback()
            raise

    def remove_member(self, department_id: int, volunteer_id: int) -> dict:
        try:
            department = self.get_department(department_id)
            member = self.repo.get_member(department_id, volunteer_id)
            if not member:
                raise NotFoundError("Wolontariusz nie należy do tego działu")
            self.repo.remove_member(member)
            self.repo.commit(skip_audit=True)
            return self._serialize_detail(department)
        except Exception:
            self.repo.rollback()
            raise

    def list_inventory(self, department_id: int) -> list[dict]:
        self.get_department(department_id)
        return [
            self._serialize_inventory_item(item, volunteer)
            for item, volunteer in self.repo.list_inventory(department_id)
        ]

    def create_inventory_item(self, department_id: int, **values) -> dict:
        try:
            department = self.get_department(department_id)
            if department.is_archived:
                raise ValidationException(
                    "Nie można dodawać przedmiotów do zarchiwizowanego działu"
                )
            self._validate_inventory_volunteer(
                values.get("borrowed_by_volunteer_id")
            )
            item = self.repo.create_inventory_item(department_id, **values)
            self.repo.flush()
            self.repo.commit(skip_audit=True)
            return self._serialize_inventory_item(
                item,
                self._inventory_volunteer(item.borrowed_by_volunteer_id),
            )
        except Exception:
            self.repo.rollback()
            raise

    def update_inventory_item(
        self, department_id: int, item_id: int, **values
    ) -> dict:
        try:
            department = self.get_department(department_id)
            if department.is_archived:
                raise ValidationException(
                    "Nie można edytować magazynu zarchiwizowanego działu"
                )
            item = self.repo.get_inventory_item(department_id, item_id)
            if not item:
                raise NotFoundError("Przedmiot nie istnieje w magazynie działu")
            self._validate_inventory_volunteer(
                values.get("borrowed_by_volunteer_id")
            )
            self.repo.update_inventory_item(item, **values)
            self.repo.flush()
            self.repo.commit(skip_audit=True)
            return self._serialize_inventory_item(
                item,
                self._inventory_volunteer(item.borrowed_by_volunteer_id),
            )
        except Exception:
            self.repo.rollback()
            raise

    def delete_inventory_item(self, department_id: int, item_id: int) -> None:
        try:
            self.get_department(department_id)
            item = self.repo.get_inventory_item(department_id, item_id)
            if not item:
                raise NotFoundError("Przedmiot nie istnieje w magazynie działu")
            self.repo.delete_inventory_item(item)
            self.repo.commit(skip_audit=True)
        except Exception:
            self.repo.rollback()
            raise

    def _validate_inventory_volunteer(self, volunteer_id: int | None) -> None:
        if volunteer_id is not None and not self.repo.volunteer_exists(volunteer_id):
            raise NotFoundError("Wolontariusz nie istnieje")

    def _inventory_volunteer(self, volunteer_id: int | None) -> Volunteer | None:
        if volunteer_id is None:
            return None
        return self.repo.get_volunteer(volunteer_id)

    def _volunteer_for_user(self, user: User) -> Volunteer:
        email = getattr(user, "email", None)
        volunteer = self.repo.get_volunteer_by_email(email) if email else None
        if not volunteer:
            raise NotFoundError(
                "Twoje konto nie jest powiązane z profilem wolontariusza"
            )
        return volunteer

    def _serialize_list_item(self, department: Department, member_count: int) -> dict:
        return {
            "id": department.id,
            "name": department.name,
            "icon": department.icon,
            "description": department.description,
            "is_archived": department.is_archived,
            "member_count": member_count,
        }

    def _serialize_detail(self, department: Department) -> dict:
        members = [
            {
                "id": member.id,
                "volunteer_id": volunteer.id,
                "full_name": volunteer.full_name,
                "email": volunteer.email,
                "status": volunteer.status,
                "membership_status": member.status,
                "created_at": member.created_at,
            }
            for member, volunteer in self.repo.list_members(department.id)
        ]
        return {
            "id": department.id,
            "name": department.name,
            "icon": department.icon,
            "description": department.description,
            "is_archived": department.is_archived,
            "created_at": department.created_at,
            "updated_at": department.updated_at,
            "members": members,
        }

    @staticmethod
    def _serialize_inventory_item(
        item: DepartmentInventoryItem, volunteer: Volunteer | None
    ) -> dict:
        return {
            "id": item.id,
            "department_id": item.department_id,
            "name": item.name,
            "location": item.location,
            "borrowed_by_volunteer_id": item.borrowed_by_volunteer_id,
            "borrowed_by_volunteer_name": volunteer.full_name if volunteer else None,
            "borrowed_at": item.borrowed_at,
            "created_at": item.created_at,
            "updated_at": item.updated_at,
        }
