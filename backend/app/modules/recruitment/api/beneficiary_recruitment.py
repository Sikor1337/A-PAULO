"""Public and staff API for beneficiary recruitment (PAP-90)."""

from fastapi import APIRouter, Depends, Query, status

from app.modules.core_data.models import User
from app.modules.recruitment.beneficiary_access import get_beneficiary_frontend_path
from app.modules.recruitment.dependencies import (
    get_beneficiary_recruitment_service,
    require_beneficiary_recruitment_access,
)
from app.modules.recruitment.public_rate_limit import (
    rate_limit_public_beneficiary_form,
)
from app.modules.recruitment.schemas.beneficiary_recruitment import (
    BeneficiaryRecruitmentCreateBeneficiaryRequest,
    BeneficiaryRecruitmentDecisionRequest,
    BeneficiaryRecruitmentFormResponse,
    BeneficiaryRecruitmentFormUpdateRequest,
    BeneficiaryRecruitmentSubmissionCreate,
    BeneficiaryRecruitmentSubmissionResponse,
)
from app.modules.recruitment.schemas.recruitment import RecruitmentFieldResponse
from app.modules.recruitment.services import BeneficiaryRecruitmentService
from app.modules.security.dependencies import require_permission
from app.modules.security.models.constants import (
    CAN_MANAGE_RECRUITMENT,
    CAN_VIEW_RECRUITMENT,
)

router = APIRouter(prefix="/beneficiary-recruitment", tags=["beneficiary-recruitment"])


@router.get("/public/form", response_model=BeneficiaryRecruitmentFormResponse)
def get_public_form(
    service: BeneficiaryRecruitmentService = Depends(
        get_beneficiary_recruitment_service
    ),
    _access: str = Depends(require_beneficiary_recruitment_access),
    _rate_limit: None = Depends(rate_limit_public_beneficiary_form),
):
    return service.get_public_form()


@router.post(
    "/public/submissions",
    response_model=BeneficiaryRecruitmentSubmissionResponse,
    status_code=status.HTTP_201_CREATED,
)
def submit_public_form(
    request: BeneficiaryRecruitmentSubmissionCreate,
    service: BeneficiaryRecruitmentService = Depends(
        get_beneficiary_recruitment_service
    ),
    _access: str = Depends(require_beneficiary_recruitment_access),
    _rate_limit: None = Depends(rate_limit_public_beneficiary_form),
):
    return service.submit(request)


@router.get("/access-link", response_model=dict[str, str])
def get_access_link(
    _user: User = Depends(require_permission(CAN_VIEW_RECRUITMENT)),
):
    return {"path": get_beneficiary_frontend_path()}


@router.get("/fields", response_model=list[RecruitmentFieldResponse])
def list_fields(
    service: BeneficiaryRecruitmentService = Depends(
        get_beneficiary_recruitment_service
    ),
    _user: User = Depends(require_permission(CAN_VIEW_RECRUITMENT)),
):
    return service.list_fields()


@router.put("/fields", response_model=list[RecruitmentFieldResponse])
def save_fields(
    request: BeneficiaryRecruitmentFormUpdateRequest,
    service: BeneficiaryRecruitmentService = Depends(
        get_beneficiary_recruitment_service
    ),
    _user: User = Depends(require_permission(CAN_MANAGE_RECRUITMENT)),
):
    return service.save_fields(request.fields)


@router.get(
    "/submissions", response_model=list[BeneficiaryRecruitmentSubmissionResponse]
)
def list_submissions(
    include_archived: bool = Query(False),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: BeneficiaryRecruitmentService = Depends(
        get_beneficiary_recruitment_service
    ),
    _user: User = Depends(require_permission(CAN_VIEW_RECRUITMENT)),
):
    return service.list_submissions(
        include_archived=include_archived,
        skip=skip,
        limit=limit,
    )


@router.post(
    "/submissions/{submission_id}/create-beneficiary",
    response_model=BeneficiaryRecruitmentSubmissionResponse,
)
def create_beneficiary(
    submission_id: int,
    request: BeneficiaryRecruitmentCreateBeneficiaryRequest,
    service: BeneficiaryRecruitmentService = Depends(
        get_beneficiary_recruitment_service
    ),
    user: User = Depends(require_permission(CAN_MANAGE_RECRUITMENT)),
):
    return service.create_beneficiary(submission_id, user, request.group_id)


@router.post(
    "/submissions/{submission_id}/reject",
    response_model=BeneficiaryRecruitmentSubmissionResponse,
)
def reject_submission(
    submission_id: int,
    request: BeneficiaryRecruitmentDecisionRequest,
    service: BeneficiaryRecruitmentService = Depends(
        get_beneficiary_recruitment_service
    ),
    _user: User = Depends(require_permission(CAN_MANAGE_RECRUITMENT)),
):
    return service.reject(submission_id, request.comment)


@router.post(
    "/submissions/{submission_id}/archive",
    response_model=BeneficiaryRecruitmentSubmissionResponse,
)
def archive_submission(
    submission_id: int,
    service: BeneficiaryRecruitmentService = Depends(
        get_beneficiary_recruitment_service
    ),
    _user: User = Depends(require_permission(CAN_MANAGE_RECRUITMENT)),
):
    return service.archive(submission_id)


@router.delete("/submissions/{submission_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_submission(
    submission_id: int,
    service: BeneficiaryRecruitmentService = Depends(
        get_beneficiary_recruitment_service
    ),
    _user: User = Depends(require_permission(CAN_MANAGE_RECRUITMENT)),
):
    service.delete(submission_id)
