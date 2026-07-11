"""Security schemas."""

from .auth import (
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
from .permissions import (
    GroupIdsRequest,
    MyPermissionsResponse,
    PermissionCodesRequest,
    PermissionResponse,
    UserGroupCreateRequest,
    UserGroupResponse,
    UserGroupSaveRequest,
    UserGroupUpdateRequest,
    UserIdsRequest,
)

__all__ = [
    "EmailRequest",
    "GroupIdsRequest",
    "LoginRequest",
    "MyPermissionsResponse",
    "PasswordResetConfirmRequest",
    "PermissionCodesRequest",
    "PermissionResponse",
    "ProfileUpdateRequest",
    "RegisterRequest",
    "Token",
    "TokenOnlyRequest",
    "TokenRefresh",
    "UserGroupCreateRequest",
    "UserGroupResponse",
    "UserGroupSaveRequest",
    "UserGroupUpdateRequest",
    "UserIdsRequest",
    "UserResponse",
]
