"""Dependencies for PI domain."""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.audit import AuditPort
from app.core.dependencies import get_db
from app.modules.audit.dependencies import get_audit_service
from app.modules.pi.repositories import (
    BeneficiaryAssignmentRepository,
    BeneficiaryRepository,
    FunctionRepository,
    GroupRepository,
    VolunteerRepository,
)
from app.modules.pi.services.beneficiaries import BeneficiaryService
from app.modules.pi.services.functions import FunctionService
from app.modules.pi.services.groups import BeneficiaryAssignmentService, GroupService
from app.modules.pi.services.imports import CsvImportService
from app.modules.pi.services.volunteers import VolunteerService


def get_volunteer_repository(
    session: Session = Depends(get_db),
) -> VolunteerRepository:
    return VolunteerRepository(session)


def get_beneficiary_repository(
    session: Session = Depends(get_db),
) -> BeneficiaryRepository:
    return BeneficiaryRepository(session)


def get_group_repository(session: Session = Depends(get_db)) -> GroupRepository:
    return GroupRepository(session)


def get_assignment_repository(
    session: Session = Depends(get_db),
) -> BeneficiaryAssignmentRepository:
    return BeneficiaryAssignmentRepository(session)


def get_function_repository(
    session: Session = Depends(get_db),
) -> FunctionRepository:
    return FunctionRepository(session)


def get_volunteer_service(
    repo: VolunteerRepository = Depends(get_volunteer_repository),
    audit: AuditPort = Depends(get_audit_service),
) -> VolunteerService:
    """Get volunteer service dependency."""
    return VolunteerService(repo, audit)


def get_beneficiary_service(
    repo: BeneficiaryRepository = Depends(get_beneficiary_repository),
    audit: AuditPort = Depends(get_audit_service),
) -> BeneficiaryService:
    """Get beneficiary service dependency."""
    return BeneficiaryService(repo, audit)


def get_group_service(
    repo: GroupRepository = Depends(get_group_repository),
    audit: AuditPort = Depends(get_audit_service),
) -> GroupService:
    """Get group service dependency."""
    return GroupService(repo, audit)


def get_assignment_service(
    repo: BeneficiaryAssignmentRepository = Depends(get_assignment_repository),
    audit: AuditPort = Depends(get_audit_service),
) -> BeneficiaryAssignmentService:
    """Get assignment service dependency."""
    return BeneficiaryAssignmentService(repo, audit)


def get_function_service(
    repo: FunctionRepository = Depends(get_function_repository),
) -> FunctionService:
    return FunctionService(repo)


def get_import_service(
    volunteer_repo: VolunteerRepository = Depends(get_volunteer_repository),
    beneficiary_repo: BeneficiaryRepository = Depends(get_beneficiary_repository),
) -> CsvImportService:
    """Get CSV import service dependency."""
    return CsvImportService(volunteer_repo, beneficiary_repo)
