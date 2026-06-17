"""User repository for data access."""
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.modules.core_data.models.user import User


class UserRepository:
    """Repository for User model database operations."""

    def __init__(self, session: Session):
        self.session = session

    def get_by_username(self, username: str) -> User | None:
        """Get user by username."""
        stmt = select(User).where(User.username == username)
        return self.session.execute(stmt).scalar_one_or_none()

    def get_by_email(self, email: str) -> User | None:
        """Get user by email."""
        stmt = select(User).where(User.email == email)
        return self.session.execute(stmt).scalar_one_or_none()

    def get_by_id(self, user_id: int) -> User | None:
        """Get user by ID."""
        return self.session.query(User).filter(User.id == user_id).first()

    def create(self, username: str, email: str, hashed_password: str, first_name: str = "", last_name: str = "") -> User:
        """Create new user."""
        user = User(
            username=username,
            email=email,
            hashed_password=hashed_password,
            first_name=first_name,
            last_name=last_name,
        )
        self.session.add(user)
        return user

    def exists(self, username: str = None, email: str = None) -> bool:
        """Check if user exists by username or email."""
        if username:
            return self.get_by_username(username) is not None
        if email:
            return self.get_by_email(email) is not None
        return False
