"""FastAPI dependency wiring for audit ports."""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.audit import AuditPort, AuditReaderPort
from app.core.dependencies import get_db
from app.modules.audit.repositories.audit import AuditRepository
from app.modules.audit.services.audit import SqlAuditService


def get_audit_repository(session: Session = Depends(get_db)) -> AuditRepository:
    return AuditRepository(session)


def get_audit_service(
    repository: AuditRepository = Depends(get_audit_repository),
) -> AuditPort:
    return SqlAuditService(repository)


def get_audit_reader(
    repository: AuditRepository = Depends(get_audit_repository),
) -> AuditReaderPort:
    return SqlAuditService(repository)
