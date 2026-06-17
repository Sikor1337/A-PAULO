"""Dependencies for PI domain."""
from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.modules.pi.services.volunteers import VolunteerService
from app.modules.pi.services.beneficiaries import BeneficiaryService
from app.modules.pi.services.groups import GroupService, BeneficiaryAssignmentService


def get_volunteer_service(session: Session = Depends(get_db)) -> VolunteerService:
    """Get volunteer service dependency."""
    return VolunteerService(session)


def get_beneficiary_service(session: Session = Depends(get_db)) -> BeneficiaryService:
    """Get beneficiary service dependency."""
    return BeneficiaryService(session)


def get_group_service(session: Session = Depends(get_db)) -> GroupService:
    """Get group service dependency."""
    return GroupService(session)


def get_assignment_service(session: Session = Depends(get_db)) -> BeneficiaryAssignmentService:
    """Get assignment service dependency."""
    return BeneficiaryAssignmentService(session)
