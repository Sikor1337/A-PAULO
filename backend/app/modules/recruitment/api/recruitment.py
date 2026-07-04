"""HTTP API for the volunteer recruitment module."""

from fastapi import APIRouter, Depends, Query, status

from app.modules.core_data.models import User
from app.modules.recruitment.dependencies import get_recruitment_service
from app.modules.recruitment.schemas import (
    DecisionRequest,
    RecruitmentFieldResponse,
    RecruitmentFormResponse,
    RecruitmentFormUpdateRequest,
    RecruitmentSubmissionCreate,
    RecruitmentSubmissionResponse,
    ReturnSubmissionRequest,
)
from app.modules.recruitment.services import RecruitmentService
from app.modules.security.dependencies import get_current_user, require_permission
from app.modules.security.models.constants import CAN_MANAGE_RECRUITMENT, CAN_VIEW_RECRUITMENT

router = APIRouter(prefix="/recruitment", tags=["recruitment"])


@router.get("/form", response_model=RecruitmentFormResponse)
def get_application_form(
    service: RecruitmentService = Depends(get_recruitment_service),
    user: User = Depends(get_current_user),
):
    submission = service.get_submission_for_user(user.id)
    initial_answers = (
        {answer["key"]: answer.get("value") for answer in submission.answers}
        if submission
        else {}
    )
    applicant_name = " ".join(
        part for part in (user.first_name, user.last_name) if part
    ) or user.username
    return RecruitmentFormResponse(
        fields=service.list_fields(active_only=True),
        applicant_name=applicant_name,
        applicant_email=user.email,
        initial_answers=initial_answers,
        submission_status=submission.status if submission else None,
        return_reason=submission.return_reason if submission else None,
    )


@router.post(
    "/submissions",
    response_model=RecruitmentSubmissionResponse,
    status_code=status.HTTP_201_CREATED,
)
def submit_application(
    request: RecruitmentSubmissionCreate,
    service: RecruitmentService = Depends(get_recruitment_service),
    user: User = Depends(get_current_user),
):
    return service.submit(user, request)


@router.get("/fields", response_model=list[RecruitmentFieldResponse])
def list_fields(
    service: RecruitmentService = Depends(get_recruitment_service),
    _user: User = Depends(require_permission(CAN_VIEW_RECRUITMENT)),
):
    return service.list_fields()


@router.put("/fields", response_model=list[RecruitmentFieldResponse])
def save_fields(
    request: RecruitmentFormUpdateRequest,
    service: RecruitmentService = Depends(get_recruitment_service),
    _user: User = Depends(require_permission(CAN_MANAGE_RECRUITMENT)),
):
    return service.save_fields(request.fields)


@router.get("/submissions", response_model=list[RecruitmentSubmissionResponse])
def list_submissions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    submission_status: str | None = Query(default=None, alias="status"),
    search: str | None = None,
    service: RecruitmentService = Depends(get_recruitment_service),
    _user: User = Depends(require_permission(CAN_VIEW_RECRUITMENT)),
):
    return service.list_submissions(
        skip=skip, limit=limit, status=submission_status, search=search
    )


@router.get(
    "/submissions/{submission_id}", response_model=RecruitmentSubmissionResponse
)
def get_submission(
    submission_id: int,
    service: RecruitmentService = Depends(get_recruitment_service),
    _user: User = Depends(require_permission(CAN_VIEW_RECRUITMENT)),
):
    return service.get_submission(submission_id)


@router.post(
    "/submissions/{submission_id}/start-onboarding",
    response_model=RecruitmentSubmissionResponse,
)
def start_onboarding(
    submission_id: int,
    service: RecruitmentService = Depends(get_recruitment_service),
    _user: User = Depends(require_permission(CAN_MANAGE_RECRUITMENT)),
):
    return service.move_to_onboarding(submission_id)


@router.post(
    "/submissions/{submission_id}/return", response_model=RecruitmentSubmissionResponse
)
def return_submission(
    submission_id: int,
    request: ReturnSubmissionRequest,
    service: RecruitmentService = Depends(get_recruitment_service),
    _user: User = Depends(require_permission(CAN_MANAGE_RECRUITMENT)),
):
    return service.return_submission(submission_id, request.reason)


@router.post(
    "/submissions/{submission_id}/accept", response_model=RecruitmentSubmissionResponse
)
def accept_submission(
    submission_id: int,
    request: DecisionRequest,
    service: RecruitmentService = Depends(get_recruitment_service),
    _user: User = Depends(require_permission(CAN_MANAGE_RECRUITMENT)),
):
    return service.accept(submission_id, request.comment)


@router.post(
    "/submissions/{submission_id}/reject", response_model=RecruitmentSubmissionResponse
)
def reject_submission(
    submission_id: int,
    request: DecisionRequest,
    service: RecruitmentService = Depends(get_recruitment_service),
    _user: User = Depends(require_permission(CAN_MANAGE_RECRUITMENT)),
):
    return service.reject(submission_id, request.comment)


@router.post(
    "/submissions/{submission_id}/restore-onboarding",
    response_model=RecruitmentSubmissionResponse,
)
def restore_onboarding(
    submission_id: int,
    service: RecruitmentService = Depends(get_recruitment_service),
    _user: User = Depends(require_permission(CAN_MANAGE_RECRUITMENT)),
):
    return service.restore_to_onboarding(submission_id)
