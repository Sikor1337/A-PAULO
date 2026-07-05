"""Token lifecycle and feed publication rules."""

import hashlib
import secrets
from datetime import UTC, datetime

from app.core.errors import NotFoundError
from app.modules.calendar.models import CalendarFeedToken
from app.modules.calendar.models.constants import PUBLISHED_STATUS
from app.modules.calendar.repositories import (
    CalendarAuditRepository,
    CalendarEventRepository,
    CalendarFeedTokenRepository,
)
from app.modules.core_data.models import User
from app.modules.security.models.constants import CAN_MANAGE_EVENTS, CAN_VIEW_EVENTS
from app.modules.security.services.permissions import PermissionService


def hash_feed_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class CalendarSubscriptionService:
    def __init__(
        self,
        tokens: CalendarFeedTokenRepository,
        events: CalendarEventRepository,
        audit: CalendarAuditRepository,
        permissions: PermissionService,
    ):
        self.tokens = tokens
        self.events = events
        self.audit = audit
        self.permissions = permissions

    def status(self, user: User) -> CalendarFeedToken | None:
        token = self.tokens.get_by_user_id(user.id)
        return token if token and token.is_active else None

    def generate(self, user: User) -> tuple[str, CalendarFeedToken]:
        try:
            plain_token = secrets.token_urlsafe(32)
            token_hash = hash_feed_token(plain_token)
            record = self.tokens.get_by_user_id(user.id)
            if record:
                record.token_hash = token_hash
                record.is_active = True
                record.created_at = datetime.now(UTC)
                record.revoked_at = None
            else:
                record = self.tokens.create(user_id=user.id, token_hash=token_hash)
            self.audit.add(
                actor_id=user.id,
                action="generated",
                entity_type="feed_token",
            )
            self.tokens.commit()
            self.tokens.refresh(record)
            return plain_token, record
        except Exception:
            self.tokens.rollback()
            raise

    def revoke(self, user: User) -> None:
        try:
            record = self.tokens.get_by_user_id(user.id)
            if record and record.is_active:
                record.is_active = False
                record.revoked_at = datetime.now(UTC)
                self.audit.add(
                    actor_id=user.id,
                    action="revoked",
                    entity_type="feed_token",
                )
                self.tokens.commit()
        except Exception:
            self.tokens.rollback()
            raise

    def events_for_token(self, plain_token: str):
        record = self.tokens.get_active_by_hash(hash_feed_token(plain_token))
        if (
            not record
            or not record.user.is_active
            or not self.permissions.has_permission(record.user, CAN_VIEW_EVENTS)
        ):
            raise NotFoundError("Feed kalendarza nie istnieje")
        events = self.events.list_visible(
            is_admin=self.permissions.has_permission(record.user, CAN_MANAGE_EVENTS),
            limit=1000,
        )
        return [
            event for event in events if event.status in {PUBLISHED_STATUS, "cancelled"}
        ]
