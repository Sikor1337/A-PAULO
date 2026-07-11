"""Data access for one-time e-mail tokens (PAP-87)."""

from datetime import datetime

from sqlalchemy.orm import Session

from app.infrastructure.sql.repository import SQLRepository
from app.modules.security.models.email_tokens import EmailToken


class EmailTokenRepository(SQLRepository):
    def __init__(self, session: Session):
        self.session = session

    def create(
        self,
        *,
        user_id: int,
        purpose: str,
        token_hash: str,
        expires_at: datetime,
    ) -> EmailToken:
        token = EmailToken(
            user_id=user_id,
            purpose=purpose,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self.session.add(token)
        return token

    def get_active_by_hash(self, purpose: str, token_hash: str) -> EmailToken | None:
        """Get an unused token by hash; expiry is checked by the service."""
        return (
            self.session.query(EmailToken)
            .filter(
                EmailToken.purpose == purpose,
                EmailToken.token_hash == token_hash,
                EmailToken.used_at.is_(None),
            )
            .first()
        )

    def latest_for_user(self, user_id: int, purpose: str) -> EmailToken | None:
        return (
            self.session.query(EmailToken)
            .filter(
                EmailToken.user_id == user_id,
                EmailToken.purpose == purpose,
            )
            .order_by(EmailToken.created_at.desc(), EmailToken.id.desc())
            .first()
        )

    def invalidate_for_user(self, user_id: int, purpose: str, when: datetime) -> None:
        """Mark every outstanding token of one purpose as used."""
        self.session.query(EmailToken).filter(
            EmailToken.user_id == user_id,
            EmailToken.purpose == purpose,
            EmailToken.used_at.is_(None),
        ).update({"used_at": when})
