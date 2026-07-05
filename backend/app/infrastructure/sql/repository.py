"""Shared SQL repository transaction boundary."""

from typing import Any

from sqlalchemy.orm import Session

from app.modules.audit.session import AuditAwareSession


class SQLRepository:
    """Own SQLAlchemy access so services never depend on Session."""

    def __init__(self, session: Session):
        self.session = session

    def flush(self) -> None:
        self.session.flush()

    def commit(self, *, skip_audit: bool = False) -> None:
        if isinstance(self.session, AuditAwareSession):
            self.session.commit(skip_audit=skip_audit)
            return
        # Unit and integration tests may deliberately provide a vanilla Session.
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()

    def refresh(self, entity: Any) -> None:
        self.session.refresh(entity)
