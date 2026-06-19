"""Authentication API endpoints."""
from fastapi import APIRouter, Depends

from app.modules.core_data.models import User
from app.modules.security.dependencies import get_auth_service, get_current_user
from app.modules.security.schemas import (
    LoginRequest,
    ProfileUpdateRequest,
    RegisterRequest,
    Token,
    TokenRefresh,
    UserResponse,
)
from app.modules.security.services.auth import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse)
def register(data: RegisterRequest, svc: AuthService = Depends(get_auth_service)):
    """Register new user."""
    return svc.register(
        username=data.username,
        email=data.email,
        password=data.password,
        first_name=data.first_name,
        last_name=data.last_name,
    )


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
