"""HTTP API for the volunteer recruitment module."""

from fastapi import APIRouter, Depends, Query, status

from app.modules.core_data.models import User
from app.modules.recruitment.dependencies import get_recruitment_service
from app.modules.recruitment.schemas import (
    RecruitmentFieldCreate,
    RecruitmentFieldOrderRequest,
    RecruitmentFieldResponse,
    RecruitmentFieldUpdate,
    RecruitmentFormResponse,
    RecruitmentInvitationCreate,
    RecruitmentInvitationResponse,
    RecruitmentPublicFormResponse,
    RecruitmentSubmissionCreate,
    RecruitmentSubmissionResponse,
    ReturnSubmissionRequest,
)
from app.modules.recruitment.services import RecruitmentService
from app.modules.security.dependencies import get_current_user

router = APIRouter(prefix="/recruitment", tags=["recruitment"])


@router.get("/form", response_model=RecruitmentFormResponse)
def get_public_form(service: RecruitmentService = Depends(get_recruitment_service)):
    return RecruitmentFormResponse(fields=service.list_fields(active_only=True))


@router.get("/form/{invitation_token}", response_model=RecruitmentPublicFormResponse)
def get_invited_public_form(
    invitation_token: str,
    service: RecruitmentService = Depends(get_recruitment_service),
):
    invitation = service.get_public_invitation(invitation_token)
    return RecruitmentPublicFormResponse(
        fields=service.list_fields(active_only=True),
        invitation_token=invitation.token,
        recipient_name=invitation.recipient_name,
        recipient_email=invitation.recipient_email,
        return_reason=(
            invitation.submission.return_reason if invitation.submission else None
        ),
    )


@router.post(
    "/submissions/{invitation_token}",
    response_model=RecruitmentSubmissionResponse,
    status_code=status.HTTP_201_CREATED,
)
def submit_public_form(
    invitation_token: str,
    request: RecruitmentSubmissionCreate,
    service: RecruitmentService = Depends(get_recruitment_service),
):
    return service.submit(invitation_token, request.answers)


@router.get("/fields", response_model=list[RecruitmentFieldResponse])
def list_fields(
    service: RecruitmentService = Depends(get_recruitment_service),
    _user: User = Depends(get_current_user),
):
    return service.list_fields()


@router.post(
    "/fields",
    response_model=RecruitmentFieldResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_field(
    request: RecruitmentFieldCreate,
    service: RecruitmentService = Depends(get_recruitment_service),
    _user: User = Depends(get_current_user),
):
    return service.create_field(**request.model_dump())


@router.put("/fields/order", response_model=list[RecruitmentFieldResponse])
def reorder_fields(
    request: RecruitmentFieldOrderRequest,
    service: RecruitmentService = Depends(get_recruitment_service),
    _user: User = Depends(get_current_user),
):
    return service.reorder_fields(request.field_ids)


@router.patch("/fields/{field_id}", response_model=RecruitmentFieldResponse)
def update_field(
    field_id: int,
    request: RecruitmentFieldUpdate,
    service: RecruitmentService = Depends(get_recruitment_service),
    _user: User = Depends(get_current_user),
):
    return service.update_field(field_id, **request.model_dump(exclude_unset=True))


@router.delete("/fields/{field_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_field(
    field_id: int,
    service: RecruitmentService = Depends(get_recruitment_service),
    _user: User = Depends(get_current_user),
):
    service.delete_field(field_id)


@router.get("/invitations", response_model=list[RecruitmentInvitationResponse])
def list_invitations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: RecruitmentService = Depends(get_recruitment_service),
    _user: User = Depends(get_current_user),
):
    return service.list_invitations(skip=skip, limit=limit)


@router.post(
    "/invitations",
    response_model=RecruitmentInvitationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_invitation(
    request: RecruitmentInvitationCreate,
    service: RecruitmentService = Depends(get_recruitment_service),
    _user: User = Depends(get_current_user),
):
    return service.create_invitation(**request.model_dump())


@router.delete("/invitations/{invitation_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_invitation(
    invitation_id: int,
    service: RecruitmentService = Depends(get_recruitment_service),
    _user: User = Depends(get_current_user),
):
    service.revoke_invitation(invitation_id)


@router.get("/submissions", response_model=list[RecruitmentSubmissionResponse])
def list_submissions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    submission_status: str | None = Query(default=None, alias="status"),
    search: str | None = None,
    service: RecruitmentService = Depends(get_recruitment_service),
    _user: User = Depends(get_current_user),
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
    _user: User = Depends(get_current_user),
):
    return service.get_submission(submission_id)


@router.post(
    "/submissions/{submission_id}/start-onboarding",
    response_model=RecruitmentSubmissionResponse,
)
def start_onboarding(
    submission_id: int,
    service: RecruitmentService = Depends(get_recruitment_service),
    _user: User = Depends(get_current_user),
):
    return service.move_to_onboarding(submission_id)


@router.post(
    "/submissions/{submission_id}/return", response_model=RecruitmentSubmissionResponse
)
def return_submission(
    submission_id: int,
    request: ReturnSubmissionRequest,
    service: RecruitmentService = Depends(get_recruitment_service),
    _user: User = Depends(get_current_user),
):
    return service.return_submission(submission_id, request.reason)


@router.post(
    "/submissions/{submission_id}/accept", response_model=RecruitmentSubmissionResponse
)
def accept_submission(
    submission_id: int,
    service: RecruitmentService = Depends(get_recruitment_service),
    _user: User = Depends(get_current_user),
):
    return service.accept(submission_id)


@router.post(
    "/submissions/{submission_id}/reject", response_model=RecruitmentSubmissionResponse
)
def reject_submission(
    submission_id: int,
    service: RecruitmentService = Depends(get_recruitment_service),
    _user: User = Depends(get_current_user),
):
    return service.reject(submission_id)
