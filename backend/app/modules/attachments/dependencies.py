"""Attachment dependencies."""

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.constants import ATTACHMENT_MAX_SIZE_BYTES
from app.core.dependencies import get_attachment_storage, get_db
from app.infrastructure.storage.attachments import AttachmentStorage
from app.modules.attachments.repositories import AttachmentRepository
from app.modules.attachments.services import AttachmentService
from app.modules.pi.repositories import (
    BeneficiaryAssignmentRepository,
    BeneficiaryRepository,
    GroupRepository,
    VolunteerRepository,
)


def get_attachment_repository(
    session: Session = Depends(get_db),
) -> AttachmentRepository:
    return AttachmentRepository(session)


def get_group_repository(session: Session = Depends(get_db)) -> GroupRepository:
    return GroupRepository(session)


def get_beneficiary_repository(
    session: Session = Depends(get_db),
) -> BeneficiaryRepository:
    return BeneficiaryRepository(session)


def get_volunteer_repository(
    session: Session = Depends(get_db),
) -> VolunteerRepository:
    return VolunteerRepository(session)


def get_assignment_repository(
    session: Session = Depends(get_db),
) -> BeneficiaryAssignmentRepository:
    return BeneficiaryAssignmentRepository(session)


def get_attachment_service(
    repo: AttachmentRepository = Depends(get_attachment_repository),
    group_repo: GroupRepository = Depends(get_group_repository),
    beneficiary_repo: BeneficiaryRepository = Depends(get_beneficiary_repository),
    volunteer_repo: VolunteerRepository = Depends(get_volunteer_repository),
    assignment_repo: BeneficiaryAssignmentRepository = Depends(
        get_assignment_repository
    ),
    storage: AttachmentStorage = Depends(get_attachment_storage),
) -> AttachmentService:
    """Build attachment service with the configured storage backend."""
    return AttachmentService(
        repo=repo,
        group_repo=group_repo,
        beneficiary_repo=beneficiary_repo,
        volunteer_repo=volunteer_repo,
        assignment_repo=assignment_repo,
        storage=storage,
        max_size_bytes=ATTACHMENT_MAX_SIZE_BYTES,
    )
