"""API for the permission catalog and user security groups."""

from fastapi import APIRouter, Depends, Response, status

from app.modules.core_data.models import User
from app.modules.security.dependencies import (
    get_current_user,
    get_permission_service,
    require_permission,
)
from app.modules.security.models.constants import CAN_MANAGE_SECURITY, CAN_VIEW_SECURITY
from app.modules.security.schemas import (
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
from app.modules.security.services import PermissionService

router = APIRouter(prefix="/security", tags=["security-permissions"])


@router.get("/me/permissions", response_model=MyPermissionsResponse)
def my_permissions(
    user: User = Depends(get_current_user),
    service: PermissionService = Depends(get_permission_service),
):
    return MyPermissionsResponse(
        permissions=sorted(service.permissions_for_user(user)),
        group_ids=service.group_ids_for_user(user.id),
    )


@router.get("/permissions", response_model=list[PermissionResponse])
def list_permissions(
    _user: User = Depends(require_permission(CAN_VIEW_SECURITY)),
    service: PermissionService = Depends(get_permission_service),
):
    return service.list_permissions()


@router.get("/groups", response_model=list[UserGroupResponse])
def list_groups(
    _user: User = Depends(require_permission(CAN_VIEW_SECURITY)),
    service: PermissionService = Depends(get_permission_service),
):
    return service.list_groups()


@router.post(
    "/groups", response_model=UserGroupResponse, status_code=status.HTTP_201_CREATED
)
def create_group(
    request: UserGroupCreateRequest,
    _user: User = Depends(require_permission(CAN_MANAGE_SECURITY)),
    service: PermissionService = Depends(get_permission_service),
):
    return service.create_group(**request.model_dump())


@router.patch("/groups/{group_id}", response_model=UserGroupResponse)
def update_group(
    group_id: int,
    request: UserGroupUpdateRequest,
    _user: User = Depends(require_permission(CAN_MANAGE_SECURITY)),
    service: PermissionService = Depends(get_permission_service),
):
    return service.update_group(group_id, **request.model_dump(exclude_unset=True))


@router.put("/groups/{group_id}", response_model=UserGroupResponse)
def save_group(
    group_id: int,
    request: UserGroupSaveRequest,
    _user: User = Depends(require_permission(CAN_MANAGE_SECURITY)),
    service: PermissionService = Depends(get_permission_service),
):
    return service.save_group(group_id, **request.model_dump())


@router.put("/groups/{group_id}/permissions", response_model=UserGroupResponse)
def replace_group_permissions(
    group_id: int,
    request: PermissionCodesRequest,
    _user: User = Depends(require_permission(CAN_MANAGE_SECURITY)),
    service: PermissionService = Depends(get_permission_service),
):
    return service.replace_group_permissions(group_id, request.permission_codes)


@router.put("/groups/{group_id}/users", response_model=UserGroupResponse)
def replace_group_users(
    group_id: int,
    request: UserIdsRequest,
    _user: User = Depends(require_permission(CAN_MANAGE_SECURITY)),
    service: PermissionService = Depends(get_permission_service),
):
    return service.replace_group_users(group_id, request.user_ids)


@router.delete("/groups/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_group(
    group_id: int,
    _user: User = Depends(require_permission(CAN_MANAGE_SECURITY)),
    service: PermissionService = Depends(get_permission_service),
):
    service.delete_group(group_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/users/{user_id}/groups", response_model=list[int])
def user_groups(
    user_id: int,
    _user: User = Depends(require_permission(CAN_VIEW_SECURITY)),
    service: PermissionService = Depends(get_permission_service),
):
    return service.group_ids_for_user(user_id)


@router.put("/users/{user_id}/groups", response_model=list[int])
def replace_user_groups(
    user_id: int,
    request: GroupIdsRequest,
    _user: User = Depends(require_permission(CAN_MANAGE_SECURITY)),
    service: PermissionService = Depends(get_permission_service),
):
    return service.replace_user_groups(user_id, request.group_ids)
