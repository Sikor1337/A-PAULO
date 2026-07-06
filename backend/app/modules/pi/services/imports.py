"""CSV bulk-import service for PI domain.

Import contract (PAP-81):
- the whole file is validated first; any format error blocks the import,
- duplicates (existing or repeated within the file) are skipped and reported,
- rows are numbered by CSV file line, where the header is line 1.
"""

import csv
import io
import re
from datetime import date, datetime, time

from app.core.errors import ValidationException
from app.modules.pi.repositories.beneficiaries import BeneficiaryRepository
from app.modules.pi.repositories.volunteers import VolunteerRepository
from app.modules.pi.schemas.imports import ImportReport, ImportRowIssue

MAX_FILE_BYTES = 2 * 1024 * 1024
MAX_ROWS = 5000

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

VOLUNTEER_STATUSES = ("Aktywny", "Były")
BENEFICIARY_STATUSES = ("OBECNY", "ZMARŁY", "BYŁY", "DPS_ZOL")
_TRUE_WORDS = frozenset({"tak", "true", "1"})
_FALSE_WORDS = frozenset({"nie", "false", "0", ""})

VOLUNTEER_COLUMNS = (
    "Imię i nazwisko",
    "Email",
    "Telefon",
    "Link społecznościowy",
    "Status",
    "Data przystąpienia",
    "Notatki",
)
VOLUNTEER_REQUIRED = ("imię i nazwisko", "email")

BENEFICIARY_COLUMNS = (
    "Imię i nazwisko",
    "Adres",
    "Telefon",
    "Telefon rodziny",
    "Status",
    "BO",
    "Ostatnia wizyta księdza",
    "Ostatnie spotkanie wolontariusza",
    "Opis",
)
BENEFICIARY_REQUIRED = ("imię i nazwisko", "adres")

VOLUNTEER_TEMPLATE_CSV = ";".join(VOLUNTEER_COLUMNS) + "\r\n"
BENEFICIARY_TEMPLATE_CSV = ";".join(BENEFICIARY_COLUMNS) + "\r\n"


def _decode(data: bytes) -> str:
    if b"\x00" in data:
        raise ValidationException("Plik nie wygląda na tekstowy plik CSV")
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        return data.decode("cp1250", errors="replace")


def _parse_rows(
    data: bytes, known_columns: tuple[str, ...], required: tuple[str, ...]
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
    known = {column.lower() for column in known_columns}
    unknown = [raw for raw in raw_headers if raw and raw.lower() not in known]
    if unknown:
        raise ValidationException(
            f"Nieznane kolumny: {', '.join(unknown)}. Pobierz aktualną formatkę."
        )
    missing = [column for column in required if column not in headers]
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


class _RowReader:
    """Field-level validation for a single CSV row, collecting Polish messages."""

    def __init__(
        self, line_number: int, fields: dict[str, str], errors: list[ImportRowIssue]
    ):
        self.line_number = line_number
        self.fields = fields
        self.errors = errors
        self.valid = True

    def _fail(self, message: str) -> None:
        self.errors.append(ImportRowIssue(row=self.line_number, message=message))
        self.valid = False

    def text(self, header: str, *, required: bool = False, max_length: int) -> str:
        value = self.fields.get(header, "")
        if required and not value:
            self._fail(f"Pole „{header}” jest wymagane")
        elif len(value) > max_length:
            self._fail(f"Pole „{header}” może mieć najwyżej {max_length} znaków")
        return value

    def email(self, header: str) -> str:
        value = self.text(header, required=True, max_length=255)
        if value and not _EMAIL_RE.match(value):
            self._fail(f"Nieprawidłowy adres email: {value}")
        return value

    def choice(self, header: str, allowed: tuple[str, ...], default: str) -> str:
        value = self.fields.get(header, "")
        if not value:
            return default
        for option in allowed:
            if value.lower() == option.lower():
                return option
        self._fail(f"Pole „{header}” musi być jednym z: {', '.join(allowed)}")
        return default

    def flag(self, header: str) -> bool:
        value = self.fields.get(header, "").lower()
        if value in _TRUE_WORDS:
            return True
        if value in _FALSE_WORDS:
            return False
        self._fail(f"Pole „{header}” musi być TAK lub NIE")
        return False

    def date(self, header: str) -> date | None:
        value = self.fields.get(header, "")
        if not value:
            return None
        try:
            return _parse_date(value)
        except ValueError:
            self._fail(
                f"Pole „{header}” ma nieprawidłową datę (użyj RRRR-MM-DD): {value}"
            )
            return None


class CsvImportService:
    """Bulk CSV import of volunteers and beneficiaries."""

    def __init__(
        self,
        volunteer_repo: VolunteerRepository,
        beneficiary_repo: BeneficiaryRepository,
    ):
        self.volunteer_repo = volunteer_repo
        self.beneficiary_repo = beneficiary_repo

    def import_volunteers(self, data: bytes) -> ImportReport:
        rows = _parse_rows(data, VOLUNTEER_COLUMNS, VOLUNTEER_REQUIRED)
        errors: list[ImportRowIssue] = []
        parsed: list[tuple[int, dict]] = []
        for line_number, fields in rows:
            reader = _RowReader(line_number, fields, errors)
            payload = {
                "full_name": reader.text(
                    "imię i nazwisko", required=True, max_length=200
                ),
                "email": reader.email("email"),
                "phone": reader.text("telefon", max_length=20) or None,
                "social_link": reader.text("link społecznościowy", max_length=500)
                or None,
                "status": reader.choice("status", VOLUNTEER_STATUSES, "Aktywny"),
                "join_date": datetime.combine(
                    reader.date("data przystąpienia") or date.today(), time.min
                ),
                "notes": fields.get("notatki", ""),
            }
            if reader.valid:
                parsed.append((line_number, payload))

        skipped: list[ImportRowIssue] = []
        to_create: list[dict] = []
        existing = {email.lower() for email in self.volunteer_repo.list_emails()}
        seen: set[str] = set()
        for line_number, payload in parsed:
            key = payload["email"].lower()
            if key in existing:
                skipped.append(
                    ImportRowIssue(
                        row=line_number,
                        message=(
                            f"Wolontariusz z adresem {payload['email']} "
                            "już istnieje — pominięto"
                        ),
                    )
                )
            elif key in seen:
                skipped.append(
                    ImportRowIssue(
                        row=line_number,
                        message=(
                            f"Adres {payload['email']} powtarza się "
                            "w pliku — pominięto"
                        ),
                    )
                )
            else:
                seen.add(key)
                to_create.append(payload)

        return self._finalize(self.volunteer_repo, rows, to_create, skipped, errors)

    def import_beneficiaries(self, data: bytes) -> ImportReport:
        rows = _parse_rows(data, BENEFICIARY_COLUMNS, BENEFICIARY_REQUIRED)
        errors: list[ImportRowIssue] = []
        parsed: list[tuple[int, dict]] = []
        for line_number, fields in rows:
            reader = _RowReader(line_number, fields, errors)
            payload = {
                "full_name": reader.text(
                    "imię i nazwisko", required=True, max_length=200
                ),
                "address": reader.text("adres", required=True, max_length=500),
                "phone": reader.text("telefon", max_length=20) or None,
                "family_phone": reader.text("telefon rodziny", max_length=20) or None,
                "status": reader.choice("status", BENEFICIARY_STATUSES, "OBECNY"),
                "bo_enrolled": reader.flag("bo"),
                "last_priest_visit": reader.date("ostatnia wizyta księdza"),
                "last_volunteer_meeting": reader.date(
                    "ostatnie spotkanie wolontariusza"
                ),
                "description": fields.get("opis", ""),
            }
            if reader.valid:
                parsed.append((line_number, payload))

        skipped: list[ImportRowIssue] = []
        to_create: list[dict] = []
        existing = {
            " ".join(name.split()).lower()
            for name in self.beneficiary_repo.list_full_names()
        }
        seen: set[str] = set()
        for line_number, payload in parsed:
            key = " ".join(payload["full_name"].split()).lower()
            if key in existing:
                skipped.append(
                    ImportRowIssue(
                        row=line_number,
                        message=(
                            f"Podopieczny {payload['full_name']} "
                            "już istnieje — pominięto"
                        ),
                    )
                )
            elif key in seen:
                skipped.append(
                    ImportRowIssue(
                        row=line_number,
                        message=(
                            f"{payload['full_name']} powtarza się "
                            "w pliku — pominięto"
                        ),
                    )
                )
            else:
                seen.add(key)
                to_create.append(payload)

        return self._finalize(self.beneficiary_repo, rows, to_create, skipped, errors)

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
