"""Authentication service for users."""
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AuthenticationError, ConflictError
from app.modules.core_data.models.user import User
from app.modules.core_data.repositories.users import UserRepository

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
        self, username: str, email: str, password: str, first_name: str = "", last_name: str = ""
    ) -> User:
        """Register new user."""
        try:
            # Check if user already exists
            if self.user_repo.exists(username=username):
                raise ConflictError(f"Username '{username}' already exists")
            if self.user_repo.exists(email=email):
                raise ConflictError(f"Email '{email}' already exists")

            hashed_password = self.hash_password(password)
            user = self.user_repo.create(
                username=username,
                email=email,
                hashed_password=hashed_password,
                first_name=first_name,
                last_name=last_name,
            )
            self.session.flush()
            self.session.refresh(user)
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
