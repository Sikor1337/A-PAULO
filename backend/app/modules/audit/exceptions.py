"""Audit-specific exceptions."""


class MissingAuditRecordError(RuntimeError):
    """Raised when a guarded transaction is committed without an audit entry."""
