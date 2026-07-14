"""CSV import schemas for PI domain."""

from pydantic import BaseModel, Field


class ImportRowIssue(BaseModel):
    """A single problem tied to a CSV file line (header is line 1)."""

    row: int
    message: str


class ImportReport(BaseModel):
    """Outcome of a CSV import: either errors (nothing imported) or counts."""

    ok: bool
    total_rows: int
    imported: int
    skipped: list[ImportRowIssue] = Field(default_factory=list)
    errors: list[ImportRowIssue] = Field(default_factory=list)
