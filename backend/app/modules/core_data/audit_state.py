"""Audit state snapshots for core_data domain entities."""

from app.core.audit import audit_value
from app.modules.core_data.models import User


def user_audit_state(user: User) -> dict:
	"""Capture user state for audit comparison."""
	return {
		"username": audit_value(user.username),
		"email": audit_value(user.email),
		"first_name": audit_value(user.first_name),
		"last_name": audit_value(user.last_name),
		"status": audit_value(user.status),
		"is_active": audit_value(user.is_active),
	}
