"""Security schemas."""

from .auth import (
    LoginRequest,
    ProfileUpdateRequest,
    RegisterRequest,
    Token,
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
    UserGroupUpdateRequest,
    UserIdsRequest,
)

__all__ = [
    "GroupIdsRequest",
    "LoginRequest",
    "MyPermissionsResponse",
    "PermissionCodesRequest",
    "PermissionResponse",
    "ProfileUpdateRequest",
    "RegisterRequest",
    "Token",
    "TokenRefresh",
    "UserGroupCreateRequest",
    "UserGroupResponse",
    "UserGroupUpdateRequest",
    "UserIdsRequest",
    "UserResponse",
]
