"""Users API endpoints."""
from fastapi import APIRouter, Depends, Header
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.modules.core_data.schemas.users import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenResponse,
    UserResponse,
)
from app.modules.core_data.services.users import UserService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse)
def register(
    request: UserRegisterRequest,
    session: Session = Depends(get_db),
):
    """Register new user."""
    service = UserService(session)
    user = service.register_user(
        username=request.username,
        email=request.email,
        password=request.password,
        first_name=request.first_name,
        last_name=request.last_name,
    )
    return user


@router.post("/token", response_model=TokenResponse)
def login(
    request: UserLoginRequest,
    session: Session = Depends(get_db),
):
    """Login user and get tokens."""
    service = UserService(session)
    user = service.authenticate_user(request.username, request.password)
    access_token = service.create_access_token(user.id)
    # For now, refresh token is same as access token (can be extended)
    refresh_token = access_token
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.get("/user", response_model=UserResponse)
def get_current_user(
    authorization: str = Header(None),
    session: Session = Depends(get_db),
):
    """Get current authenticated user."""
    if not authorization or not authorization.startswith("Bearer "):
        from app.core.errors import AuthenticationError
        raise AuthenticationError("Missing or invalid authorization header")

    token = authorization.split(" ")[1]
    service = UserService(session)
    user = service.get_current_user(token)
    return user
