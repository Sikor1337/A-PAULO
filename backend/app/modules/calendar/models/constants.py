"""Calendar domain constants."""

DEFAULT_TIMEZONE = "Europe/Warsaw"

EVENT_STATUSES = ("draft", "published", "cancelled")
EVENT_VISIBILITIES = ("organization", "admins")

PUBLISHED_STATUS = "published"
DRAFT_STATUS = "draft"
CANCELLED_STATUS = "cancelled"
ORGANIZATION_VISIBILITY = "organization"
ADMIN_VISIBILITY = "admins"

EVENT_AUDIT_ACTIONS = ("created", "updated", "cancelled", "deleted")
TOKEN_AUDIT_ACTIONS = ("generated", "revoked")
