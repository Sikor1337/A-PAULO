"""Core data repositories - data access layer."""

from app.modules.core_data.repositories.users import UserRepository
from app.modules.core_data.repositories.roles import RoleRepository

__all__ = ["UserRepository", "RoleRepository"]
