"""Department business logic."""

from app.core.errors import ConflictError, NotFoundError, ValidationException
from app.modules.departments.models.departments import Department
from app.modules.departments.repositories.departments import DepartmentRepository


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
            self.repo.add_member(department_id, volunteer_id)
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
