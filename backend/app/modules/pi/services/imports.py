"""CSV bulk-import service for PI domain.

Import contract (PAP-81):
- the whole file is validated first; any format error blocks the import,
- duplicates (existing or repeated within the file) are skipped and reported,
- rows are numbered by CSV file line, where the header is line 1.

Column definitions (`VOLUNTEER_COLUMNS` / `BENEFICIARY_COLUMNS`) are the single
source of truth: they drive both the downloadable template and row parsing, and
take field lengths from the SQLAlchemy models and statuses from the PI enums.
"""

import csv
import io
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, time
from enum import Enum
from typing import Any

from app.core.errors import ValidationException
from app.core.uploads import MEGABYTE, ensure_upload_size
from app.core.validation import is_valid_email
from app.infrastructure.sql.base import Base
from app.modules.pi.models import Beneficiary, Volunteer
from app.modules.pi.models.enums import BeneficiaryStatus, VolunteerStatus
from app.modules.pi.repositories.beneficiaries import BeneficiaryRepository
from app.modules.pi.repositories.volunteers import VolunteerRepository
from app.modules.pi.schemas.imports import ImportReport, ImportRowIssue

MAX_FILE_BYTES = 2 * MEGABYTE
MAX_ROWS = 5000

_TRUE_WORDS = frozenset({"tak", "true", "1"})
_FALSE_WORDS = frozenset({"nie", "false", "0", ""})


def _is_true_word(value: str) -> bool:
    return value.lower() in _TRUE_WORDS


def _is_false_word(value: str) -> bool:
    return value.lower() in _FALSE_WORDS


def _column_length(model: type[Base], field: str) -> int:
    """Max length of a string column, read from the model definition."""
    return model.__table__.columns[field].type.length


class RowValidationError(Exception):
    """Single-field validation failure; the message is the user-facing warning."""


class _RowReader:
    """Field-level parsing for a single CSV row; failures raise RowValidationError."""

    def __init__(self, fields: dict[str, str]):
        self.fields = fields

    def raw(self, header: str) -> str:
        return self.fields.get(header, "")

    def text(self, header: str, *, required: bool = False, max_length: int) -> str:
        value = self.raw(header)
        if required and not value:
            raise RowValidationError(f"Pole „{header}” jest wymagane")
        if len(value) > max_length:
            raise RowValidationError(
                f"Pole „{header}” może mieć najwyżej {max_length} znaków"
            )
        return value

    def email(self, header: str, *, max_length: int) -> str:
        value = self.text(header, required=True, max_length=max_length)
        if value and not is_valid_email(value):
            raise RowValidationError(f"Nieprawidłowy adres email: {value}")
        return value

    def choice(self, header: str, allowed: type[Enum], default: Enum) -> str:
        value = self.raw(header)
        if not value:
            return default.value
        for option in allowed:
            if value.lower() == option.value.lower():
                return option.value
        raise RowValidationError(
            f"Pole „{header}” musi być jednym z: "
            f"{', '.join(option.value for option in allowed)}"
        )

    def flag(self, header: str) -> bool:
        value = self.raw(header)
        if _is_true_word(value):
            return True
        if _is_false_word(value):
            return False
        raise RowValidationError(f"Pole „{header}” musi być TAK lub NIE")

    def date(self, header: str) -> date | None:
        value = self.raw(header)
        if not value:
            return None
        try:
            return _parse_date(value)
        except ValueError:
            raise RowValidationError(
                f"Pole „{header}” ma nieprawidłową datę (użyj RRRR-MM-DD): {value}"
            ) from None


@dataclass(frozen=True)
class ColumnSpec:
    """One CSV column: template header, target model field, and row parser."""

    header: str
    field: str
    parse: Callable[[_RowReader, str], Any]
    required: bool = False


@dataclass(frozen=True)
class CsvTemplate:
    """Downloadable CSV template (filename + content)."""

    filename: str
    content: str


VOLUNTEER_COLUMNS: tuple[ColumnSpec, ...] = (
    ColumnSpec(
        "Imię i nazwisko",
        "full_name",
        lambda r, h: r.text(
            h, required=True, max_length=_column_length(Volunteer, "full_name")
        ),
        required=True,
    ),
    ColumnSpec(
        "Email",
        "email",
        lambda r, h: r.email(h, max_length=_column_length(Volunteer, "email")),
        required=True,
    ),
    ColumnSpec(
        "Telefon",
        "phone",
        lambda r, h: r.text(h, max_length=_column_length(Volunteer, "phone")) or None,
    ),
    ColumnSpec(
        "Link społecznościowy",
        "social_link",
        lambda r, h: r.text(h, max_length=_column_length(Volunteer, "social_link"))
        or None,
    ),
    ColumnSpec(
        "Status",
        "status",
        lambda r, h: r.choice(h, VolunteerStatus, VolunteerStatus.AKTYWNY),
    ),
    ColumnSpec(
        "Data przystąpienia",
        "join_date",
        lambda r, h: datetime.combine(r.date(h) or date.today(), time.min),
    ),
    ColumnSpec("Notatki", "notes", lambda r, h: r.raw(h)),
)

BENEFICIARY_COLUMNS: tuple[ColumnSpec, ...] = (
    ColumnSpec(
        "Imię i nazwisko",
        "full_name",
        lambda r, h: r.text(
            h, required=True, max_length=_column_length(Beneficiary, "full_name")
        ),
        required=True,
    ),
    ColumnSpec(
        "Adres",
        "address",
        lambda r, h: r.text(
            h, required=True, max_length=_column_length(Beneficiary, "address")
        ),
        required=True,
    ),
    ColumnSpec(
        "Telefon",
        "phone",
        lambda r, h: r.text(h, max_length=_column_length(Beneficiary, "phone"))
        or None,
    ),
    ColumnSpec(
        "Telefon rodziny",
        "family_phone",
        lambda r, h: r.text(h, max_length=_column_length(Beneficiary, "family_phone"))
        or None,
    ),
    ColumnSpec(
        "Status",
        "status",
        lambda r, h: r.choice(h, BeneficiaryStatus, BeneficiaryStatus.OBECNY),
    ),
    ColumnSpec("BO", "bo_enrolled", lambda r, h: r.flag(h)),
    ColumnSpec(
        "Ostatnia wizyta księdza", "last_priest_visit", lambda r, h: r.date(h)
    ),
    ColumnSpec(
        "Ostatnie spotkanie wolontariusza",
        "last_volunteer_meeting",
        lambda r, h: r.date(h),
    ),
    ColumnSpec("Opis", "description", lambda r, h: r.raw(h)),
)


def _template_csv(specs: tuple[ColumnSpec, ...]) -> str:
    return ";".join(spec.header for spec in specs) + "\r\n"


def _decode(data: bytes) -> str:
    if b"\x00" in data:
        raise ValidationException("Plik nie wygląda na tekstowy plik CSV")
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        return data.decode("cp1250", errors="replace")


def _parse_rows(
    data: bytes, specs: tuple[ColumnSpec, ...]
) -> list[tuple[int, dict[str, str]]]:
    """Parse CSV bytes into (line_number, {lowercase header: value}) pairs.

    Raises ValidationException for file-level problems (empty file, bad headers).
    """
    text = _decode(data)
    first_line = text.lstrip("\r\n").split("\n", 1)[0]
    delimiter = ";" if first_line.count(";") >= first_line.count(",") else ","
    reader = csv.reader(io.StringIO(text), delimiter=delimiter)
    raw_rows = [row for row in reader]
    if not raw_rows:
        raise ValidationException("Plik CSV jest pusty")

    raw_headers = [cell.strip() for cell in raw_rows[0]]
    headers = [cell.lower() for cell in raw_headers]
    known = {spec.header.lower() for spec in specs}
    unknown = [raw for raw in raw_headers if raw and raw.lower() not in known]
    if unknown:
        raise ValidationException(
            f"Nieznane kolumny: {', '.join(unknown)}. Pobierz aktualną formatkę."
        )
    missing = [
        spec.header.lower()
        for spec in specs
        if spec.required and spec.header.lower() not in headers
    ]
    if missing:
        raise ValidationException(
            f"Brak wymaganych kolumn: {', '.join(missing)}. Pobierz aktualną formatkę."
        )

    rows: list[tuple[int, dict[str, str]]] = []
    for line_number, raw in enumerate(raw_rows[1:], start=2):
        values = [cell.strip() for cell in raw]
        if not any(values):
            continue
        rows.append((line_number, dict(zip(headers, values, strict=False))))
    if len(rows) > MAX_ROWS:
        raise ValidationException(
            f"Plik ma zbyt wiele wierszy (maksymalnie {MAX_ROWS})"
        )
    return rows


def _parse_date(value: str) -> date:
    for fmt in ("%Y-%m-%d", "%d.%m.%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    raise ValueError(value)


def _parse_payload(
    line_number: int,
    fields: dict[str, str],
    specs: tuple[ColumnSpec, ...],
    errors: list[ImportRowIssue],
) -> dict[str, Any] | None:
    """Build a model payload from one row; collect issues, return None if invalid."""
    reader = _RowReader(fields)
    payload: dict[str, Any] = {}
    valid = True
    for spec in specs:
        try:
            payload[spec.field] = spec.parse(reader, spec.header.lower())
        except RowValidationError as error:
            errors.append(ImportRowIssue(row=line_number, message=str(error)))
            valid = False
    return payload if valid else None


def _split_duplicates(
    parsed: list[tuple[int, dict[str, Any]]],
    existing: set[str],
    key_of: Callable[[dict[str, Any]], str],
    already_exists: Callable[[dict[str, Any]], str],
    repeated: Callable[[dict[str, Any]], str],
) -> tuple[list[dict[str, Any]], list[ImportRowIssue]]:
    """Split parsed rows into rows to create and skipped duplicates."""
    to_create: list[dict[str, Any]] = []
    skipped: list[ImportRowIssue] = []
    seen: set[str] = set()
    for line_number, payload in parsed:
        key = key_of(payload)
        if key in existing:
            skipped.append(
                ImportRowIssue(row=line_number, message=already_exists(payload))
            )
        elif key in seen:
            skipped.append(
                ImportRowIssue(row=line_number, message=repeated(payload))
            )
        else:
            seen.add(key)
            to_create.append(payload)
    return to_create, skipped


class CsvImportService:
    """Bulk CSV import of volunteers and beneficiaries."""

    def __init__(
        self,
        volunteer_repo: VolunteerRepository,
        beneficiary_repo: BeneficiaryRepository,
    ):
        self.volunteer_repo = volunteer_repo
        self.beneficiary_repo = beneficiary_repo

    def volunteer_template(self) -> CsvTemplate:
        return CsvTemplate(
            "formatka-wolontariusze.csv", _template_csv(VOLUNTEER_COLUMNS)
        )

    def beneficiary_template(self) -> CsvTemplate:
        return CsvTemplate(
            "formatka-podopieczni.csv", _template_csv(BENEFICIARY_COLUMNS)
        )

    def import_volunteers(self, data: bytes) -> ImportReport:
        return self._run_import(
            data,
            specs=VOLUNTEER_COLUMNS,
            repo=self.volunteer_repo,
            existing_keys=lambda: {
                email.lower() for email in self.volunteer_repo.list_emails()
            },
            key_of=lambda payload: payload["email"].lower(),
            already_exists=lambda payload: (
                f"Wolontariusz z adresem {payload['email']} już istnieje — pominięto"
            ),
            repeated=lambda payload: (
                f"Adres {payload['email']} powtarza się w pliku — pominięto"
            ),
        )

    def import_beneficiaries(self, data: bytes) -> ImportReport:
        return self._run_import(
            data,
            specs=BENEFICIARY_COLUMNS,
            repo=self.beneficiary_repo,
            existing_keys=lambda: {
                " ".join(name.split()).lower()
                for name in self.beneficiary_repo.list_full_names()
            },
            key_of=lambda payload: " ".join(payload["full_name"].split()).lower(),
            already_exists=lambda payload: (
                f"Podopieczny {payload['full_name']} już istnieje — pominięto"
            ),
            repeated=lambda payload: (
                f"{payload['full_name']} powtarza się w pliku — pominięto"
            ),
        )

    def _run_import(
        self,
        data: bytes,
        *,
        specs: tuple[ColumnSpec, ...],
        repo: VolunteerRepository | BeneficiaryRepository,
        existing_keys: Callable[[], set[str]],
        key_of: Callable[[dict[str, Any]], str],
        already_exists: Callable[[dict[str, Any]], str],
        repeated: Callable[[dict[str, Any]], str],
    ) -> ImportReport:
        """Shared pipeline: validate file, parse rows, skip duplicates, persist."""
        ensure_upload_size(data, MAX_FILE_BYTES)
        rows = _parse_rows(data, specs)
        errors: list[ImportRowIssue] = []
        parsed: list[tuple[int, dict[str, Any]]] = []
        for line_number, fields in rows:
            payload = _parse_payload(line_number, fields, specs, errors)
            if payload is not None:
                parsed.append((line_number, payload))
        to_create, skipped = _split_duplicates(
            parsed, existing_keys(), key_of, already_exists, repeated
        )
        return self._finalize(repo, rows, to_create, skipped, errors)

    def _finalize(
        self,
        repo: VolunteerRepository | BeneficiaryRepository,
        rows: list,
        to_create: list[dict],
        skipped: list[ImportRowIssue],
        errors: list[ImportRowIssue],
    ) -> ImportReport:
        if errors:
            return ImportReport(
                ok=False,
                total_rows=len(rows),
                imported=0,
                skipped=skipped,
                errors=sorted(errors, key=lambda issue: issue.row),
            )
        try:
            for payload in to_create:
                repo.create(**payload)
            repo.commit(skip_audit=True)
        except Exception:
            repo.rollback()
            raise
        return ImportReport(
            ok=True,
            total_rows=len(rows),
            imported=len(to_create),
            skipped=skipped,
            errors=[],
        )
