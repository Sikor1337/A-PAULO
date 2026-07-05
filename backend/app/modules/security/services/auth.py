from fastapi import HTTPException, status

from app.core.audit import AuditEntry, AuditPort, EntityType, calculate_delta
from app.modules.core_data.audit_state import user_audit_state
from app.modules.core_data.models import User
from app.modules.core_data.repositories.users import UserRepository
from app.modules.recruitment.access import is_valid_recruitment_access_token
from app.modules.recruitment.constants import (
    MIGRATED_RECRUITMENT_PASSWORD,
    NEW_VOLUNTEER_STATUS,
    REGULAR_USER_STATUS,
)
from app.modules.security.schemas import LoginRequest, ProfileUpdateRequest, Token
from app.modules.security.services.password import hash_password, verify_password
from app.modules.security.services.permissions import PermissionService

from .token import TokenService


class AuthService:
    def __init__(
        self,
        repo: UserRepository,
        token_service: TokenService,
        permissions: PermissionService,
        audit: AuditPort,
    ):
        self.repo = repo
        self.token_service = token_service
        self.permissions = permissions
        self.audit = audit

    def _state(self, user: User) -> dict:
        return user_audit_state(user, self.permissions.group_ids_for_user(user.id))

    def _record_user(
        self,
        action: str,
        user: User,
        old_state: dict,
        new_state: dict,
        *,
        password_changed: bool = False,
    ) -> None:
        changes = calculate_delta(old_state, new_state)
        if password_changed:
            changes["password"] = {"old": "[ukryte]", "new": "[zmieniono]"}
        self.audit.record(
            AuditEntry(
                entity_type=EntityType.CORE_DATA_USER.value,
                entity_id=str(user.id),
                action=action,
                actor_id=str(user.id),
                actor_display_name=user.email,
                changes=changes,
            )
        )

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
        recruitment_token: str | None = None,
    ) -> User:
        """Register new user."""
        try:
            # Normalize inputs for consistent lookups
            normalized_username = username.strip().lower()
            normalized_email = email.strip().lower()

            if recruitment_token and not is_valid_recruitment_access_token(
                recruitment_token
            ):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail="Link rekrutacyjny jest nieprawidłowy lub nieaktualny",
                )

            # Check if user already exists
            if self.repo.get_by_username(normalized_username):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Username '{username}' already exists",
                )
            existing_email_user = self.repo.get_by_email(normalized_email)
            is_migrated_candidate = bool(
                existing_email_user
                and not existing_email_user.is_active
                and existing_email_user.hashed_password == MIGRATED_RECRUITMENT_PASSWORD
            )
            if existing_email_user and not is_migrated_candidate:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Email '{email}' already exists",
                )

            # Hash password
            hashed_password = hash_password(password)

            if is_migrated_candidate:
                assert existing_email_user is not None
                old_state = self._state(existing_email_user)
                user = self.repo.update(
                    existing_email_user,
                    username=normalized_username,
                    hashed_password=hashed_password,
                    first_name=first_name,
                    last_name=last_name,
                    status=existing_email_user.status,
                    is_active=True,
                )
            else:
                old_state = {}
                user = self.repo.create(
                    username=normalized_username,
                    email=normalized_email,
                    hashed_password=hashed_password,
                    first_name=first_name,
                    last_name=last_name,
                    status=(
                        NEW_VOLUNTEER_STATUS
                        if recruitment_token
                        else REGULAR_USER_STATUS
                    ),
                )
            self.repo.flush()
            self.repo.refresh(user)
            self.permissions.assign_default_group(user, actor=user)
            self._record_user(
                "REGISTER",
                user,
                old_state,
                self._state(user),
                password_changed=is_migrated_candidate,
            )
            self.repo.commit()
            return user
        except HTTPException:
            self.repo.rollback()
            raise
        except Exception:
            self.repo.rollback()
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

            old_state = self._state(user)
            update_fields = {
                "email": data.email,
                "first_name": data.first_name,
                "last_name": data.last_name,
            }
            if data.new_password:
                update_fields["hashed_password"] = hash_password(data.new_password)

            user = self.repo.update(user, **update_fields)
            self.repo.flush()
            self.repo.refresh(user)
            new_state = self._state(user)
            changes = calculate_delta(old_state, new_state)
            if data.new_password:
                changes["password"] = {
                    "old": "[ukryte]",
                    "new": "[zmieniono]",
                }
            if not changes:
                self.repo.rollback()
                return user
            self._record_user(
                "PROFILE_UPDATE",
                user,
                old_state,
                new_state,
                password_changed=bool(data.new_password),
            )
            self.repo.commit()
            return user
        except HTTPException:
            self.repo.rollback()
            raise
        except Exception:
            self.repo.rollback()
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
