"""Request and response schemas for permissions and user groups."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PermissionResponse(BaseModel):
    id: int
    code: str
    name: str
    category: str

    model_config = ConfigDict(from_attributes=True)


class UserGroupCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=500)
    permission_codes: list[str] = Field(default_factory=list)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Nazwa grupy nie może być pusta")
        return value


class UserGroupUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=500)

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError("Nazwa grupy nie może być pusta")
        return value


class PermissionCodesRequest(BaseModel):
    permission_codes: list[str]


class UserIdsRequest(BaseModel):
    user_ids: list[int]


class GroupIdsRequest(BaseModel):
    group_ids: list[int]


class UserGroupResponse(BaseModel):
    id: int
    name: str
    description: str
    is_system: bool
    system_key: str | None
    permissions: list[PermissionResponse]
    user_ids: list[int]
    created_at: datetime
    updated_at: datetime


class MyPermissionsResponse(BaseModel):
    permissions: list[str]
    group_ids: list[int]
