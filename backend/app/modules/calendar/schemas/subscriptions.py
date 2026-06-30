"""DTOs for private iCalendar subscriptions."""

from datetime import datetime

from pydantic import BaseModel


class FeedTokenStatusResponse(BaseModel):
    has_active_token: bool
    created_at: datetime | None = None


class FeedTokenCreatedResponse(BaseModel):
    feed_url: str
    created_at: datetime
    warning: str
