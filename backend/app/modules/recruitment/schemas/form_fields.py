"""Internal typed commands shared by configurable recruitment forms."""

from pydantic import BaseModel, Field


class FormFieldWrite(BaseModel):
    key: str = Field(..., min_length=1, max_length=100)
    label: str = Field(..., min_length=1, max_length=250)
    field_type: str = Field(..., min_length=1, max_length=30)
    required: bool
    placeholder: str = Field(default="", max_length=250)
    options: list[str] = Field(default_factory=list)
    position: int = Field(..., ge=0)
    is_active: bool
    is_system: bool
