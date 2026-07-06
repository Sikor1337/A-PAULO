"""CSV import endpoints for PI domain."""

from fastapi import APIRouter, Depends, File, Response, UploadFile

from app.core.errors import ValidationException
from app.modules.core_data.models import User
from app.modules.pi.dependencies import get_import_service
from app.modules.pi.schemas.imports import ImportReport
from app.modules.pi.services.imports import (
    BENEFICIARY_TEMPLATE_CSV,
    MAX_FILE_BYTES,
    VOLUNTEER_TEMPLATE_CSV,
    CsvImportService,
)
from app.modules.security.dependencies import require_permission
from app.modules.security.models.constants import (
    CAN_MANAGE_BENEFICIARIES,
    CAN_MANAGE_VOLUNTEERS,
)

router = APIRouter(prefix="/imports", tags=["imports"])


def _template_response(csv_text: str, filename: str) -> Response:
    return Response(
        content=csv_text.encode("utf-8-sig"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


async def _read_upload(file: UploadFile) -> bytes:
    data = await file.read()
    if len(data) > MAX_FILE_BYTES:
        raise ValidationException("Plik jest zbyt duży (maksymalnie 2 MB)")
    return data


@router.get("/volunteers/template")
def volunteer_template(
    _user: User = Depends(require_permission(CAN_MANAGE_VOLUNTEERS)),
):
    """Download the CSV template for volunteer import."""
    return _template_response(VOLUNTEER_TEMPLATE_CSV, "formatka-wolontariusze.csv")


@router.post("/volunteers", response_model=ImportReport)
async def import_volunteers(
    file: UploadFile = File(...),
    service: CsvImportService = Depends(get_import_service),
    _user: User = Depends(require_permission(CAN_MANAGE_VOLUNTEERS)),
):
    """Validate and import volunteers from a CSV file."""
    return service.import_volunteers(await _read_upload(file))


@router.get("/beneficiaries/template")
def beneficiary_template(
    _user: User = Depends(require_permission(CAN_MANAGE_BENEFICIARIES)),
):
    """Download the CSV template for beneficiary import."""
    return _template_response(BENEFICIARY_TEMPLATE_CSV, "formatka-podopieczni.csv")


@router.post("/beneficiaries", response_model=ImportReport)
async def import_beneficiaries(
    file: UploadFile = File(...),
    service: CsvImportService = Depends(get_import_service),
    _user: User = Depends(require_permission(CAN_MANAGE_BENEFICIARIES)),
):
    """Validate and import beneficiaries from a CSV file."""
    return service.import_beneficiaries(await _read_upload(file))
