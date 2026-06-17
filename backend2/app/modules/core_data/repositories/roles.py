"""Role repository for data access."""
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.modules.core_data.models.role import Role


class RoleRepository:
    """Repository for Role model database operations."""

    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, role_id: int) -> Role | None:
        """Get role by ID."""
        return self.session.query(Role).filter(Role.id == role_id).first()

    def get_by_name(self, name: str) -> Role | None:
        """Get role by name."""
        stmt = select(Role).where(Role.name == name)
        return self.session.execute(stmt).scalar_one_or_none()

    def list_all(self, skip: int = 0, limit: int = 100, name: str = None, is_active: bool = None) -> list[Role]:
        """List roles with optional filters."""
        query = self.session.query(Role)

        if name:
            query = query.filter(Role.name.ilike(f"%{name}%"))
        if is_active is not None:
            query = query.filter(Role.is_active == is_active)

        return query.order_by(Role.name).offset(skip).limit(limit).all()

    def count(self, name: str = None, is_active: bool = None) -> int:
        """Count roles with optional filters."""
        query = self.session.query(func.count(Role.id))

        if name:
            query = query.filter(Role.name.ilike(f"%{name}%"))
        if is_active is not None:
            query = query.filter(Role.is_active == is_active)

        return query.scalar() or 0

    def create(self, **kwargs) -> Role:
        """Create new role."""
        role = Role(**kwargs)
        self.session.add(role)
        return role

    def update(self, role: Role, **kwargs) -> Role:
        """Update role."""
        for key, value in kwargs.items():
            if hasattr(role, key):
                setattr(role, key, value)
        return role

    def delete(self, role: Role) -> None:
        """Delete role."""
        self.session.delete(role)
