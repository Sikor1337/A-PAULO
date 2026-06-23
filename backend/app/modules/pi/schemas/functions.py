"""Function schemas for PI domain."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class FunctionCreateRequest(BaseModel):
    """Function creation request."""

    name: str = Field(..., min_length=1, max_length=100)


class FunctionUpdateRequest(BaseModel):
    """Function update request."""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    is_active: Optional[bool] = None


class FunctionResponse(BaseModel):
    """Function response DTO."""

    id: int
    name: str
    is_system: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
