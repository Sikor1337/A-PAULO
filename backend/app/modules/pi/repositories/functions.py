"""Function repository for data access."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.infrastructure.sql.repository import SQLRepository
from app.modules.pi.models.function import Function


class FunctionRepository(SQLRepository):
    """Repository for Function model database operations."""

    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, function_id: int) -> Function | None:
        """Get function by ID."""
        return self.session.query(Function).filter(Function.id == function_id).first()

    def get_by_name(self, name: str) -> Function | None:
        """Get function by name."""
        stmt = select(Function).where(func.lower(Function.name) == name.lower())
        return self.session.execute(stmt).scalar_one_or_none()

    def list_all(
        self,
        skip: int = 0,
        limit: int = 100,
        name: str | None = None,
        is_active: bool | None = None,
    ) -> list[Function]:
        """List functions with optional filters."""
        query = self.session.query(Function)

        if name:
            query = query.filter(Function.name.ilike(f"%{name}%"))
        if is_active is not None:
            query = query.filter(Function.is_active == is_active)

        return query.order_by(Function.name).offset(skip).limit(limit).all()

    def count(self, name: str | None = None, is_active: bool | None = None) -> int:
        """Count functions with optional filters."""
        query = self.session.query(func.count(Function.id))

        if name:
            query = query.filter(Function.name.ilike(f"%{name}%"))
        if is_active is not None:
            query = query.filter(Function.is_active == is_active)

        return query.scalar() or 0

    def create(self, *, name: str) -> Function:
        """Create new function."""
        function = Function(name=name)
        self.session.add(function)
        return function

    def update(
        self,
        function: Function,
        *,
        name: str | None,
        is_active: bool | None,
    ) -> Function:
        """Update function."""
        if name is not None:
            function.name = name
        if is_active is not None:
            function.is_active = is_active
        return function

    def delete(self, function: Function) -> None:
        """Delete function."""
        self.session.delete(function)
