"""Authentication service for users."""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AuthenticationError, ConflictError, NotFoundError
from app.modules.core_data.models.user import User
from app.modules.core_data.repositories.users import UserRepository
from app.modules.security.services.permissions import PermissionService
from app.modules.security.services.password import hash_password

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserService:
    """Service for user authentication operations."""

    def __init__(self, session: Session):
        self.session = session
        self.user_repo = UserRepository(session)
        self.settings = get_settings()

    def hash_password(self, password: str) -> str:
        """Hash a password."""
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash."""
        return pwd_context.verify(plain_password, hashed_password)

    def register_user(
        self,
        username: str,
        email: str,
        password: str,
        first_name: str = "",
        last_name: str = "",
        status: str = "regular",
    ) -> User:
        """Register new user."""
        try:
            normalized_username = username.strip().lower()
            normalized_email = email.strip().lower()

            # Check if user already exists
            if self.user_repo.exists(username=normalized_username):
                raise ConflictError(f"Username '{username}' already exists")
            if self.user_repo.exists(email=normalized_email):
                raise ConflictError(f"Email '{email}' already exists")

            hashed_password = self.hash_password(password)
            user = self.user_repo.create(
                username=normalized_username,
                email=normalized_email,
                hashed_password=hashed_password,
                first_name=first_name,
                last_name=last_name,
                status=status,
            )
            self.session.flush()
            self.session.refresh(user)
            PermissionService(self.session).assign_default_group(user)
            self.session.commit()
            return user
        except Exception:
            self.session.rollback()
            raise

    def authenticate_user(self, username: str, password: str) -> User:
        """Authenticate user by username or email."""
        # Try to find by username first, then by email
        user = self.user_repo.get_by_username(username)
        if not user:
            user = self.user_repo.get_by_email(username)

        if not user or not self.verify_password(password, user.hashed_password):
            raise AuthenticationError("Invalid username/email or password")

        if not user.is_active:
            raise AuthenticationError("User account is inactive")

        return user

    def create_access_token(self, user_id: int) -> str:
        """Create JWT access token."""
        data = {
            "sub": str(user_id),
            "type": "access",
        }
        expires_delta = timedelta(minutes=self.settings.access_token_expire_minutes)
        expire = datetime.utcnow() + expires_delta
        data["exp"] = expire
        encoded_jwt = jwt.encode(
            data,
            self.settings.secret_key,
            algorithm=self.settings.algorithm,
        )
        return encoded_jwt

    def verify_token(self, token: str) -> int:
        """Verify JWT token and return user_id."""
        try:
            payload = jwt.decode(
                token,
                self.settings.secret_key,
                algorithms=[self.settings.algorithm],
            )
            user_id: str = payload.get("sub")
            if user_id is None:
                raise AuthenticationError("Invalid token")
            return int(user_id)
        except JWTError:
            raise AuthenticationError("Invalid token")

    def get_current_user(self, token: str) -> User:
        """Get current user from token."""
        user_id = self.verify_token(token)
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise AuthenticationError("User not found")
        return user

    def get_user_by_id(self, user_id: int) -> User:
        """Get user by ID or raise NotFoundError."""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError(f"User with ID {user_id} not found")
        return user

    def list_users(
        self,
        skip: int = 0,
        limit: int = 100,
        search: str | None = None,
        status: str | None = None,
        is_active: bool | None = None,
    ):
        """List users with pagination and filters."""
        users = self.user_repo.list_all(
            skip=skip,
            limit=limit,
            search=search,
            status=status,
            is_active=is_active,
        )
        count = self.user_repo.count(
            search=search,
            status=status,
            is_active=is_active,
        )
        return users, count

    def create_user(
        self,
        username: str,
        email: str,
        password: str,
        first_name: str = "",
        last_name: str = "",
        status: str = "regular",
        is_active: bool = True,
    ) -> User:
        """Create a user from the admin panel."""
        try:
            normalized_username = username.strip().lower()
            normalized_email = email.strip().lower()

            if self.user_repo.get_by_username(normalized_username):
                raise ConflictError(f"Username '{username}' already exists")
            if self.user_repo.get_by_email(normalized_email):
                raise ConflictError(f"Email '{email}' already exists")

            user = self.user_repo.create(
                username=normalized_username,
                email=normalized_email,
                hashed_password=hash_password(password),
                first_name=first_name,
                last_name=last_name,
                status=status,
                is_active=is_active,
            )
            self.session.flush()
            self.session.refresh(user)
            PermissionService(self.session).assign_default_group(user)
            self.session.commit()
            return user
        except Exception:
            self.session.rollback()
            raise

    def update_user(self, user_id: int, **kwargs) -> User:
        """Update a user from the admin panel."""
        try:
            user = self.get_user_by_id(user_id)
            update_data = {
                key: value for key, value in kwargs.items() if value is not None
            }

            if "username" in update_data:
                update_data["username"] = update_data["username"].strip().lower()
                existing = self.user_repo.get_by_username(update_data["username"])
                if existing and existing.id != user.id:
                    raise ConflictError(
                        f"Username '{kwargs['username']}' already exists"
                    )

            if "email" in update_data:
                update_data["email"] = update_data["email"].strip().lower()
                existing = self.user_repo.get_by_email(update_data["email"])
                if existing and existing.id != user.id:
                    raise ConflictError(f"Email '{kwargs['email']}' already exists")

            password = update_data.pop("password", None)
            if password:
                update_data["hashed_password"] = hash_password(password)

            user = self.user_repo.update(user, **update_data)
            self.session.flush()
            self.session.refresh(user)
            self.session.commit()
            return user
        except Exception:
            self.session.rollback()
            raise

    def delete_user(self, user_id: int, current_user_id: int | None = None) -> None:
        """Delete a user from the admin panel."""
        if current_user_id == user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot delete your own account",
            )

        try:
            user = self.get_user_by_id(user_id)
            self.user_repo.delete(user)
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise
