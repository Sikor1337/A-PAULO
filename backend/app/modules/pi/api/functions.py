"""Functions API endpoints for PI domain."""

from fastapi import APIRouter, Depends, Query

from app.modules.core_data.models import User
from app.modules.pi.dependencies import get_function_service
from app.modules.pi.schemas.functions import (
    FunctionCreateRequest,
    FunctionResponse,
    FunctionUpdateRequest,
)
from app.modules.pi.services.functions import FunctionService
from app.modules.security.dependencies import require_permission
from app.modules.security.models.constants import (
    CAN_MANAGE_FUNCTIONS,
    CAN_VIEW_FUNCTIONS,
)

router = APIRouter(prefix="/functions", tags=["functions"])


@router.get("", response_model=list[FunctionResponse])
def list_functions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    name: str | None = Query(None),
    is_active: bool | None = Query(True),
    service: FunctionService = Depends(get_function_service),
    _user: User = Depends(require_permission(CAN_VIEW_FUNCTIONS)),
):
    """List all functions with optional filters."""
    functions, _ = service.list_functions(
        skip=skip, limit=limit, name=name, is_active=is_active
    )
    return functions


@router.post("", response_model=FunctionResponse)
def create_function(
    request: FunctionCreateRequest,
    service: FunctionService = Depends(get_function_service),
    _user: User = Depends(require_permission(CAN_MANAGE_FUNCTIONS)),
):
    """Create new function."""
    return service.create_function(**request.model_dump())


@router.patch("/{function_id}", response_model=FunctionResponse)
def update_function(
    function_id: int,
    request: FunctionUpdateRequest,
    service: FunctionService = Depends(get_function_service),
    _user: User = Depends(require_permission(CAN_MANAGE_FUNCTIONS)),
):
    """Update function."""
    return service.update_function(
        function_id, **request.model_dump(exclude_unset=True)
    )


@router.delete("/{function_id}")
def delete_function(
    function_id: int,
    service: FunctionService = Depends(get_function_service),
    _user: User = Depends(require_permission(CAN_MANAGE_FUNCTIONS)),
):
    """Delete function."""
    service.delete_function(function_id)
    return {"message": "Function deleted successfully"}
