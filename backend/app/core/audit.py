"""Stable audit contracts shared by business modules."""

from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum
from typing import Any, Protocol


class EntityType(StrEnum):
    """Canonical identifiers for auditable business entities."""

    CORE_DATA_USER = "core_data_user"
    PI_VOLUNTEER = "pi_volunteer"
    PI_BENEFICIARY = "pi_beneficiary"
    PI_GROUP = "pi_group"
    PI_BENEFICIARY_ASSIGNMENT = "pi_beneficiary_assignment"
    SECURITY_USER_GROUP = "security_user_group"
    RECRUITMENT_SUBMISSION = "recruitment_submission"
    RECRUITMENT_DEPARTURE = "recruitment_departure"
    CALENDAR_EVENT = "calendar_event"
    ATTACHMENT = "attachment"


@dataclass(frozen=True, slots=True)
class AuditEntry:
    """A single immutable description of a business change."""

    entity_type: str
    entity_id: str
    action: str
    actor_id: str
    actor_display_name: str | None
    changes: dict[str, Any]
    context_type: str | None = None
    context_id: str | None = None


class AuditPort(Protocol):
    """Write contract injected into business services."""

    def record(self, entry: AuditEntry) -> None: ...


class AuditReaderPort(Protocol):
    """Read contract used by permission-aware business endpoints."""

    def get_logs_for_entity(
        self,
        entity_type: str,
        entity_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Any]: ...

    def get_logs_for_context(
        self,
        context_type: str,
        context_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Any]: ...

    def get_logs_for_entity_or_context(
        self,
        entity_type: str,
        entity_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Any]: ...


def audit_value(value: Any) -> Any:
    """Convert common domain values into deterministic JSON-compatible values."""

    if isinstance(value, datetime | date):
        return value.isoformat()
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, dict):
        return {str(key): audit_value(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [audit_value(item) for item in value]
    if isinstance(value, set):
        return [audit_value(item) for item in sorted(value, key=str)]
    return value


def calculate_delta(
    old_state: dict[str, Any], new_state: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    """Return only changed, added and removed fields."""

    delta: dict[str, dict[str, Any]] = {}
    ordered_keys = dict.fromkeys((*old_state, *new_state))
    for key in ordered_keys:
        old_value = old_state.get(key)
        new_value = new_state.get(key)
        if key not in old_state or key not in new_state or old_value != new_value:
            delta[key] = {
                "old": audit_value(old_value),
                "new": audit_value(new_value),
            }
    return delta
