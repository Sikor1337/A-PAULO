"""Authentication API endpoints."""
from fastapi import APIRouter, Depends, Response, status

from app.modules.core_data.models import User
from app.modules.security.dependencies import (
    get_account_email_service,
    get_auth_service,
    get_current_user,
)
from app.modules.security.schemas import (
    EmailRequest,
    LoginRequest,
    PasswordResetConfirmRequest,
    ProfileUpdateRequest,
    RegisterRequest,
    Token,
    TokenOnlyRequest,
    TokenRefresh,
    UserResponse,
)
from app.modules.security.services.account_emails import AccountEmailService
from app.modules.security.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse)
def register(
    data: RegisterRequest,
    svc: AuthService = Depends(get_auth_service),
    emails: AccountEmailService = Depends(get_account_email_service),
):
    """Register new user; unverified accounts get a confirmation e-mail."""
    user = svc.register(
        username=data.username,
        email=data.email,
        password=data.password,
        first_name=data.first_name,
        last_name=data.last_name,
        recruitment_token=data.recruitment_token,
    )
    if user.email_verified_at is None:
        emails.send_verification(user)
    return user


@router.post("/verify-email", status_code=status.HTTP_204_NO_CONTENT)
def verify_email(
    data: TokenOnlyRequest,
    emails: AccountEmailService = Depends(get_account_email_service),
):
    """Confirm an e-mail address using the token from the confirmation link."""
    emails.verify_email(data.token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/verify-email/resend", status_code=status.HTTP_202_ACCEPTED)
def resend_verification(
    data: EmailRequest,
    emails: AccountEmailService = Depends(get_account_email_service),
):
    """Re-send the confirmation e-mail; always 202 (no account disclosure)."""
    emails.resend_verification(data.email)
    return Response(status_code=status.HTTP_202_ACCEPTED)


@router.post("/password-reset/request", status_code=status.HTTP_202_ACCEPTED)
def request_password_reset(
    data: EmailRequest,
    emails: AccountEmailService = Depends(get_account_email_service),
):
    """Send a password-reset e-mail; always 202 (no account disclosure)."""
    emails.request_password_reset(data.email)
    return Response(status_code=status.HTTP_202_ACCEPTED)


@router.post("/password-reset/confirm", status_code=status.HTTP_204_NO_CONTENT)
def confirm_password_reset(
    data: PasswordResetConfirmRequest,
    emails: AccountEmailService = Depends(get_account_email_service),
):
    """Set a new password using a password-reset token."""
    emails.confirm_password_reset(data.token, data.new_password)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/token", response_model=Token)
def login(data: LoginRequest, svc: AuthService = Depends(get_auth_service)):
    """Login with username or email."""
    return svc.login(data)


@router.post("/token/refresh", response_model=Token)
def refresh_token(
    body: TokenRefresh, svc: AuthService = Depends(get_auth_service)
):
    """Refresh access token using refresh token."""
    return svc.refresh(body.refresh)


@router.get("/user", response_model=UserResponse)
def get_user(user: User = Depends(get_current_user)):
    """Get current authenticated user."""
    return user


@router.patch("/user", response_model=UserResponse)
def update_user(
    data: ProfileUpdateRequest,
    user: User = Depends(get_current_user),
    svc: AuthService = Depends(get_auth_service),
):
    """Update the current authenticated user's own profile."""
    return svc.update_profile(user, data)
