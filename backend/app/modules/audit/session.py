"""SQLAlchemy session enforcing deliberate audit decisions."""

from sqlalchemy.orm import Session

from app.modules.audit.exceptions import MissingAuditRecordError


class AuditAwareSession(Session):
    """Block commits unless an audit event exists or skipping is explicit."""

    def commit(self, skip_audit: bool = False) -> None:  # type: ignore[override]
        if not self.info.get("audit_recorded", False) and not skip_audit:
            raise MissingAuditRecordError(
                "Commit without audit record. Call audit.record() before commit() "
                "or use skip_audit=True."
            )
        try:
            super().commit()
        finally:
            self.info.pop("audit_recorded", None)

    def rollback(self) -> None:
        try:
            super().rollback()
        finally:
            self.info.pop("audit_recorded", None)
