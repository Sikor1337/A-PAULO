from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.modules.core_data.models import User
from app.modules.core_data.repositories.users import UserRepository
from app.modules.security.schemas import LoginRequest, ProfileUpdateRequest, Token
from app.modules.security.services.password import hash_password, verify_password

from .token import TokenService


class AuthService:
    def __init__(
        self,
        repo: UserRepository,
        token_service: TokenService,
        session: Optional[Session] = None,
    ):
        self.repo = repo
        self.token_service = token_service
        self.session = session or repo.session

    def _issue_tokens(self, user: User) -> Token:
        sub = {"sub": str(user.id)}
        access = self.token_service.create_access_token(sub)
        refresh = self.token_service.create_refresh_token(sub)
        return Token(access=access, refresh=refresh)

    def register(
        self,
        username: str,
        email: str,
        password: str,
        first_name: str = "",
        last_name: str = "",
    ) -> User:
        """Register new user."""
        try:
            # Normalize inputs for consistent lookups
            normalized_username = username.strip().lower()
            normalized_email = email.strip().lower()

            # Check if user already exists
            if self.repo.get_by_username(normalized_username):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Username '{username}' already exists",
                )
            if self.repo.get_by_email(normalized_email):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Email '{email}' already exists",
                )

            # Hash password
            hashed_password = hash_password(password)

            # Create user with normalized email, keep original username case
            user = self.repo.create(
                username=normalized_username,
                email=normalized_email,
                hashed_password=hashed_password,
                first_name=first_name,
                last_name=last_name,
            )
            self.session.flush()
            self.session.refresh(user)
            self.session.commit()
            return user
        except HTTPException:
            self.session.rollback()
            raise
        except Exception:
            self.session.rollback()
            raise

    def login(self, data: LoginRequest) -> Token:
        """Login user - supports username or email."""
        identifier = data.username.strip().lower()

        # Try to find by username first, then by email
        user = self.repo.get_by_username(identifier)
        if not user:
            user = self.repo.get_by_email(identifier)

        if (
            not user
            or not user.is_active
            or not verify_password(
                data.password,
                user.hashed_password,
            )
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )
        return self._issue_tokens(user)

    def update_profile(self, user: User, data: ProfileUpdateRequest) -> User:
        """Update the current user's own profile, optionally changing the password."""
        try:
            if data.new_password:
                if not data.current_password:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Podaj obecne hasło, aby je zmienić.",
                    )
                if not verify_password(data.current_password, user.hashed_password):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Nieprawidłowe obecne hasło.",
                    )

            if data.email and data.email != user.email:
                normalized_email = data.email.strip().lower()
                existing = self.repo.get_by_email(normalized_email)
                if existing and existing.id != user.id:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Email '{data.email}' already exists",
                    )
                data.email = normalized_email

            update_fields = {
                "email": data.email,
                "first_name": data.first_name,
                "last_name": data.last_name,
            }
            if data.new_password:
                update_fields["hashed_password"] = hash_password(data.new_password)

            user = self.repo.update(user, **update_fields)
            self.session.commit()
            self.session.refresh(user)
            return user
        except HTTPException:
            self.session.rollback()
            raise
        except Exception:
            self.session.rollback()
            raise

    def refresh(self, refresh_token: str) -> Token:
        payload = self.token_service.decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        user_id = payload.get("sub")
        if not isinstance(user_id, str):
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        user = self.repo.get_by_id(int(user_id))
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="User not found")
        return self._issue_tokens(user)
