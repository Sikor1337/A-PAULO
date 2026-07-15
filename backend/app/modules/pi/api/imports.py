"""CSV import endpoints for PI domain (thin HTTP layer over CsvImportService)."""

from fastapi import APIRouter, Depends, File, Response, UploadFile

from app.modules.core_data.models import User
from app.modules.pi.dependencies import get_import_service
from app.modules.pi.schemas.imports import ImportReport
from app.modules.pi.services.imports import CsvImportService, CsvTemplate
from app.modules.security.dependencies import require_permission
from app.modules.security.models.constants import (
    CAN_MANAGE_BENEFICIARIES,
    CAN_MANAGE_VOLUNTEERS,
)

router = APIRouter(prefix="/imports", tags=["imports"])


def _csv_attachment(template: CsvTemplate) -> Response:
    return Response(
        content=template.content.encode("utf-8-sig"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{template.filename}"'},
    )


@router.get("/volunteers/template")
def volunteer_template(
    service: CsvImportService = Depends(get_import_service),
    _user: User = Depends(require_permission(CAN_MANAGE_VOLUNTEERS)),
):
    """Download the CSV template for volunteer import."""
    return _csv_attachment(service.volunteer_template())


@router.post("/volunteers", response_model=ImportReport)
async def import_volunteers(
    file: UploadFile = File(...),
    service: CsvImportService = Depends(get_import_service),
    _user: User = Depends(require_permission(CAN_MANAGE_VOLUNTEERS)),
):
    """Validate and import volunteers from a CSV file."""
    return service.import_volunteers(await file.read())


@router.get("/beneficiaries/template")
def beneficiary_template(
    service: CsvImportService = Depends(get_import_service),
    _user: User = Depends(require_permission(CAN_MANAGE_BENEFICIARIES)),
):
    """Download the CSV template for beneficiary import."""
    return _csv_attachment(service.beneficiary_template())


@router.post("/beneficiaries", response_model=ImportReport)
async def import_beneficiaries(
    file: UploadFile = File(...),
    service: CsvImportService = Depends(get_import_service),
    _user: User = Depends(require_permission(CAN_MANAGE_BENEFICIARIES)),
):
    """Validate and import beneficiaries from a CSV file."""
    return service.import_beneficiaries(await file.read())
