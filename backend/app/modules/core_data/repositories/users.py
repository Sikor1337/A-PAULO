"""User repository for data access."""

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.infrastructure.sql.repository import SQLRepository
from app.modules.core_data.models.user import User


class UserRepository(SQLRepository):
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

    def list_all(
        self,
        skip: int = 0,
        limit: int = 100,
        search: str | None = None,
        status: str | None = None,
        is_active: bool | None = None,
    ) -> list[User]:
        """List users with optional search and filters."""
        query = self.session.query(User)

        if search:
            pattern = f"%{search}%"
            query = query.filter(
                or_(
                    User.username.ilike(pattern),
                    User.email.ilike(pattern),
                    User.first_name.ilike(pattern),
                    User.last_name.ilike(pattern),
                )
            )
        if status:
            query = query.filter(User.status == status)
        if is_active is not None:
            query = query.filter(User.is_active == is_active)

        return (
            query.order_by(User.last_name, User.first_name, User.email)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def count(
        self,
        search: str | None = None,
        status: str | None = None,
        is_active: bool | None = None,
    ) -> int:
        """Count users with optional search and filters."""
        query = self.session.query(func.count(User.id))

        if search:
            pattern = f"%{search}%"
            query = query.filter(
                or_(
                    User.username.ilike(pattern),
                    User.email.ilike(pattern),
                    User.first_name.ilike(pattern),
                    User.last_name.ilike(pattern),
                )
            )
        if status:
            query = query.filter(User.status == status)
        if is_active is not None:
            query = query.filter(User.is_active == is_active)

        return query.scalar() or 0

    def create(
        self,
        username: str,
        email: str,
        hashed_password: str,
        first_name: str = "",
        last_name: str = "",
        status: str = "regular",
        is_active: bool = True,
    ) -> User:
        """Create new user."""
        user = User(
            username=username,
            email=email,
            hashed_password=hashed_password,
            first_name=first_name,
            last_name=last_name,
            status=status,
            is_active=is_active,
        )
        self.session.add(user)
        return user

    def update(
        self,
        user: User,
        *,
        username: str | None = None,
        email: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        status: str | None = None,
        is_active: bool | None = None,
        hashed_password: str | None = None,
    ) -> User:
        """Update user fields."""
        if username is not None:
            user.username = username
        if email is not None:
            user.email = email
        if first_name is not None:
            user.first_name = first_name
        if last_name is not None:
            user.last_name = last_name
        if status is not None:
            user.status = status
        if is_active is not None:
            user.is_active = is_active
        if hashed_password is not None:
            user.hashed_password = hashed_password
        return user

    def exists(self, username: str | None = None, email: str | None = None) -> bool:
        """Check if user exists by username or email."""
        if username:
            return self.get_by_username(username) is not None
        if email:
            return self.get_by_email(email) is not None
        return False

    def delete(self, user: User) -> None:
        """Delete user."""
        self.session.delete(user)
