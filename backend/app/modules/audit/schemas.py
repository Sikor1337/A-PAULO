"""Schemas returned by future business-owned audit endpoints."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class AuditEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    entity_type: str
    entity_id: str
    action: str
    actor_id: str
    actor_display_name: str | None
    context_type: str | None
    context_id: str | None
    changes: dict[str, Any]
    created_at: datetime
