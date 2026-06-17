"""Service for role operations."""
from sqlalchemy.orm import Session

from app.core.errors import NotFoundError, ConflictError
from app.modules.core_data.models.role import Role
from app.modules.core_data.repositories.roles import RoleRepository


class RoleService:
    """Service for role operations."""

    def __init__(self, session: Session):
        self.session = session
        self.repo = RoleRepository(session)

    def get_role_by_id(self, role_id: int) -> Role:
        """Get role by ID or raise NotFoundError."""
        role = self.repo.get_by_id(role_id)
        if not role:
            raise NotFoundError(f"Role with ID {role_id} not found")
        return role

    def get_role_by_name(self, name: str) -> Role | None:
        """Get role by name."""
        return self.repo.get_by_name(name)

    def list_roles(self, skip: int = 0, limit: int = 100, name: str = None, is_active: bool = None):
        """List roles with pagination and filters."""
        roles = self.repo.list_all(skip=skip, limit=limit, name=name, is_active=is_active)
        count = self.repo.count(name=name, is_active=is_active)
        return roles, count

    def create_role(self, **kwargs) -> Role:
        """Create new role."""
        try:
            # Check if role with same name already exists
            if self.repo.get_by_name(kwargs.get("name")):
                raise ConflictError(f"Role '{kwargs.get('name')}' already exists")

            role = self.repo.create(**kwargs)
            self.session.flush()
            self.session.refresh(role)
            self.session.commit()
            return role
        except Exception:
            self.session.rollback()
            raise

    def update_role(self, role_id: int, **kwargs) -> Role:
        """Update role by ID."""
        try:
            role = self.get_role_by_id(role_id)

            # If name is being updated, check uniqueness (excluding current role)
            if "name" in kwargs and kwargs["name"] != role.name:
                if self.repo.get_by_name(kwargs["name"]):
                    raise ConflictError(f"Role '{kwargs['name']}' already exists")

            role = self.repo.update(role, **kwargs)
            self.session.flush()
            self.session.refresh(role)
            self.session.commit()
            return role
        except Exception:
            self.session.rollback()
            raise

    def delete_role(self, role_id: int) -> None:
        """Delete role."""
        try:
            role = self.get_role_by_id(role_id)
            self.repo.delete(role)
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise
