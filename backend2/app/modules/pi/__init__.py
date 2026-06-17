"""PI (Programa de Inclusión) domain - Volunteer management and beneficiary assistance."""

from app.modules.pi.models import Volunteer, Beneficiary, Group, BeneficiaryAssignment
from app.modules.pi.schemas import (
    VolunteerCreateRequest,
    VolunteerUpdateRequest,
    VolunteerResponse,
    BeneficiaryCreateRequest,
    BeneficiaryUpdateRequest,
    BeneficiaryResponse,
    GroupCreateRequest,
    GroupUpdateRequest,
    GroupResponse,
    GroupDetailResponse,
    BeneficiaryAssignmentCreateRequest,
    BeneficiaryAssignmentUpdateRequest,
    BeneficiaryAssignmentResponse,
)

__all__ = [
    "Volunteer",
    "Beneficiary",
    "Group",
    "BeneficiaryAssignment",
    "VolunteerCreateRequest",
    "VolunteerUpdateRequest",
    "VolunteerResponse",
    "BeneficiaryCreateRequest",
    "BeneficiaryUpdateRequest",
    "BeneficiaryResponse",
    "GroupCreateRequest",
    "GroupUpdateRequest",
    "GroupResponse",
    "GroupDetailResponse",
    "BeneficiaryAssignmentCreateRequest",
    "BeneficiaryAssignmentUpdateRequest",
    "BeneficiaryAssignmentResponse",
]
