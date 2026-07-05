"""Audit state snapshots for security domain entities."""

from app.core.audit import audit_value
from app.modules.security.models import UserGroup


def security_group_audit_state(group: UserGroup, user_ids: list[int]) -> dict:
	"""Capture user group state for audit comparison."""
	return {
		"name": audit_value(group.name),
		"description": audit_value(group.description),
		"is_system": audit_value(group.is_system),
		"system_key": audit_value(group.system_key),
		"user_ids": audit_value(sorted(user_ids)),
	}
