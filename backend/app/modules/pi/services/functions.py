"""Service for function operations."""
from sqlalchemy.orm import Session

from app.core.errors import ConflictError, NotFoundError, ValidationException
from app.modules.pi.models.function import Function
from app.modules.pi.repositories.functions import FunctionRepository


class FunctionService:
    """Service for volunteer function catalog operations."""

    def __init__(self, session: Session):
        self.session = session
        self.repo = FunctionRepository(session)

    def get_function_by_id(self, function_id: int) -> Function:
        """Get function by ID or raise NotFoundError."""
        function = self.repo.get_by_id(function_id)
        if not function:
            raise NotFoundError(f"Function with ID {function_id} not found")
        return function

    def list_functions(self, skip: int = 0, limit: int = 100, name: str = None, is_active: bool = None):
        """List functions with pagination and filters."""
        functions = self.repo.list_all(skip=skip, limit=limit, name=name, is_active=is_active)
        count = self.repo.count(name=name, is_active=is_active)
        return functions, count

    def create_function(self, **kwargs) -> Function:
        """Create new function."""
        try:
            name = kwargs.get("name", "").strip()
            if not name:
                raise ValidationException("Function name is required")
            if self.repo.get_by_name(name):
                raise ConflictError(f"Function '{name}' already exists")

            function = self.repo.create(name=name)
            self.session.flush()
            self.session.refresh(function)
            self.session.commit()
            return function
        except Exception:
            self.session.rollback()
            raise

    def update_function(self, function_id: int, **kwargs) -> Function:
        """Update function."""
        try:
            function = self.get_function_by_id(function_id)

            if "name" in kwargs and kwargs["name"] is not None:
                name = kwargs["name"].strip()
                if not name:
                    raise ValidationException("Function name is required")
                existing = self.repo.get_by_name(name)
                if existing and existing.id != function_id:
                    raise ConflictError(f"Function '{name}' already exists")
                kwargs["name"] = name

            function = self.repo.update(function, **kwargs)
            self.session.flush()
            self.session.refresh(function)
            self.session.commit()
            return function
        except Exception:
            self.session.rollback()
            raise

    def delete_function(self, function_id: int) -> None:
        """Delete function."""
        try:
            function = self.get_function_by_id(function_id)
            if function.is_system:
                raise ConflictError("System functions cannot be deleted")
            self.repo.delete(function)
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise
