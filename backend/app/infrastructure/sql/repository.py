"""Shared SQL repository transaction boundary."""

from typing import Any

from sqlalchemy.orm import Session


class SQLRepository:
    """Own SQLAlchemy access so services never depend on Session."""

    def __init__(self, session: Session):
        self.session = session

    def flush(self) -> None:
        self.session.flush()

    def commit(self) -> None:
        self.session.commit()

    def rollback(self) -> None:
        self.session.rollback()

    def refresh(self, entity: Any) -> None:
        self.session.refresh(entity)
