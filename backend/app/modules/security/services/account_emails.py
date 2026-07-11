"""E-mail verification and password-reset flows (PAP-87).

Security rules (see docs/pap-86-email-spike.md):
- only SHA-256 hashes of tokens are stored, never raw tokens,
- tokens are single-use with a TTL,
- request endpoints never reveal whether an account exists,
- issuing is throttled per user to protect the daily sending quota.
"""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from app.core.errors import ValidationException
from app.infrastructure.email.port import EmailMessage, EmailPort
from app.modules.core_data.models import User
from app.modules.core_data.repositories.users import UserRepository
from app.modules.security.models.email_tokens import EmailToken, EmailTokenPurpose
from app.modules.security.repositories.email_tokens import EmailTokenRepository
from app.modules.security.services.password import hash_password

VERIFY_TOKEN_TTL = timedelta(hours=24)
RESET_TOKEN_TTL = timedelta(hours=1)
ISSUE_THROTTLE = timedelta(seconds=60)


def _hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


class AccountEmailService:
    """Issues and consumes one-time e-mail tokens."""

    def __init__(
        self,
        tokens: EmailTokenRepository,
        users: UserRepository,
        email: EmailPort,
        frontend_base_url: str,
    ):
        self.tokens = tokens
        self.users = users
        self.email = email
        self.frontend_base_url = frontend_base_url.rstrip("/")

    # ── verification ──────────────────────────────────────────────

    def send_verification(self, user: User) -> None:
        """Issue a verification token and e-mail the confirmation link."""
        raw_token = self._issue(user, EmailTokenPurpose.VERIFY_EMAIL, VERIFY_TOKEN_TTL)
        if raw_token is None:
            return
        link = f"{self.frontend_base_url}/verify-email?token={raw_token}"
        self.email.send(
            EmailMessage(
                to=user.email,
                subject="A-PAULO: potwierdź swój adres e-mail",
                html=(
                    f"<p>Cześć {user.first_name or user.username}!</p>"
                    "<p>Dziękujemy za rejestrację w A-PAULO. Kliknij poniższy link, "
                    "aby potwierdzić swój adres e-mail (ważny 24 godziny):</p>"
                    f'<p><a href="{link}">Potwierdź adres e-mail</a></p>'
                    "<p>Jeśli to nie Ty zakładałeś konto, zignoruj tę wiadomość.</p>"
                ),
            )
        )

    def resend_verification(self, email: str) -> None:
        """Re-send the verification mail; silent when the account is unknown."""
        user = self.users.get_by_email(email.strip().lower())
        if user is None or user.email_verified_at is not None:
            return
        self.send_verification(user)

    def verify_email(self, raw_token: str) -> None:
        token = self._consume(EmailTokenPurpose.VERIFY_EMAIL, raw_token)
        try:
            user = self.users.get_by_id(token.user_id)
            if user is None:
                raise ValidationException("Link jest nieprawidłowy lub wygasł")
            now = datetime.now(UTC)
            if user.email_verified_at is None:
                user.email_verified_at = now
            token.used_at = now
            self.tokens.flush()
            self.tokens.commit(skip_audit=True)
        except Exception:
            self.tokens.rollback()
            raise

    # ── password reset ────────────────────────────────────────────

    def request_password_reset(self, email: str) -> None:
        """E-mail a reset link; silent when the account is unknown."""
        user = self.users.get_by_email(email.strip().lower())
        if user is None or not user.is_active:
            return
        raw_token = self._issue(user, EmailTokenPurpose.PASSWORD_RESET, RESET_TOKEN_TTL)
        if raw_token is None:
            return
        link = f"{self.frontend_base_url}/reset-password?token={raw_token}"
        self.email.send(
            EmailMessage(
                to=user.email,
                subject="A-PAULO: reset hasła",
                html=(
                    f"<p>Cześć {user.first_name or user.username}!</p>"
                    "<p>Otrzymaliśmy prośbę o reset hasła. Kliknij poniższy link, "
                    "aby ustawić nowe hasło (link ważny 1 godzinę):</p>"
                    f'<p><a href="{link}">Ustaw nowe hasło</a></p>'
                    "<p>Jeśli to nie Ty prosiłeś o reset, zignoruj tę wiadomość.</p>"
                ),
            )
        )

    def confirm_password_reset(self, raw_token: str, new_password: str) -> None:
        token = self._consume(EmailTokenPurpose.PASSWORD_RESET, raw_token)
        try:
            user = self.users.get_by_id(token.user_id)
            if user is None:
                raise ValidationException("Link jest nieprawidłowy lub wygasł")
            now = datetime.now(UTC)
            user.hashed_password = hash_password(new_password)
            # A reset proves control of the mailbox: also count as verification.
            if user.email_verified_at is None:
                user.email_verified_at = now
            token.used_at = now
            self.tokens.invalidate_for_user(
                user.id, EmailTokenPurpose.PASSWORD_RESET.value, now
            )
            self.tokens.flush()
            self.tokens.commit(skip_audit=True)
        except Exception:
            self.tokens.rollback()
            raise

    # ── internals ─────────────────────────────────────────────────

    def _issue(
        self, user: User, purpose: EmailTokenPurpose, ttl: timedelta
    ) -> str | None:
        """Persist a new token; None when throttled (mail is skipped)."""
        now = datetime.now(UTC)
        latest = self.tokens.latest_for_user(user.id, purpose.value)
        if latest is not None:
            created_at = latest.created_at
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=UTC)
            if now - created_at < ISSUE_THROTTLE:
                return None
        raw_token = secrets.token_urlsafe(32)
        try:
            self.tokens.create(
                user_id=user.id,
                purpose=purpose.value,
                token_hash=_hash_token(raw_token),
                expires_at=now + ttl,
            )
            self.tokens.flush()
            self.tokens.commit(skip_audit=True)
        except Exception:
            self.tokens.rollback()
            raise
        return raw_token

    def _consume(self, purpose: EmailTokenPurpose, raw_token: str) -> EmailToken:
        token = self.tokens.get_active_by_hash(purpose.value, _hash_token(raw_token))
        if token is None:
            raise ValidationException("Link jest nieprawidłowy lub wygasł")
        expires_at = token.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        if expires_at < datetime.now(UTC):
            raise ValidationException("Link jest nieprawidłowy lub wygasł")
        return token
