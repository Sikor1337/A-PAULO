"""Pydantic schemas for roles."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class RoleCreateRequest(BaseModel):
    """Role creation request."""

    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)


class RoleUpdateRequest(BaseModel):
    """Role update request."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None


class RoleResponse(BaseModel):
    """Role response DTO."""

    id: int
    name: str
    description: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
