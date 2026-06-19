"""Pydantic schemas for users."""
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserRegisterRequest(BaseModel):
    """User registration request."""

    username: str = Field(..., min_length=3, max_length=150)
    email: EmailStr
    password: str = Field(..., min_length=6)
    first_name: str = Field(default="", max_length=150)
    last_name: str = Field(default="", max_length=150)


class UserLoginRequest(BaseModel):
    """User login request - supports email or username."""

    username: str = Field(...)  # Can be username or email
    password: str = Field(...)


class TokenResponse(BaseModel):
    """Token response."""

    access: str = Field(alias="access_token")
    refresh: str = Field(alias="refresh_token")
    token_type: str = "bearer"

    model_config = ConfigDict(populate_by_name=True)


class UserResponse(BaseModel):
    """User response DTO."""

    id: int
    username: str
    email: str
    first_name: str
    last_name: str
    status: str

    model_config = ConfigDict(from_attributes=True)
