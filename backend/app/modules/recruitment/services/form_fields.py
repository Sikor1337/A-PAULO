"""Shared persistence rules for configurable recruitment form fields."""

import re
import unicodedata
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Protocol

from app.core.errors import ConflictError, NotFoundError
from app.modules.recruitment.schemas.form_fields import FormFieldWrite


class FormFieldEntity(Protocol):
    id: int
    key: str
    label: str
    field_type: str
    required: bool
    placeholder: str
    options: list[str]
    position: int
    is_active: bool
    is_system: bool


class FormFieldDraft(Protocol):
    @property
    def id(self) -> int | None: ...

    @property
    def label(self) -> str: ...

    @property
    def field_type(self) -> str: ...

    @property
    def required(self) -> bool: ...

    @property
    def placeholder(self) -> str: ...

    @property
    def options(self) -> list[str]: ...

    @property
    def is_active(self) -> bool: ...


class FormFieldRepository[FieldT: FormFieldEntity](Protocol):
    def list_fields(self, *, active_only: bool = False) -> list[FieldT]: ...

    def create_field(self, request: FormFieldWrite) -> FieldT: ...

    def delete_field(self, field: FieldT) -> None: ...

    def commit(self, *, skip_audit: bool = False) -> None: ...

    def rollback(self) -> None: ...


@dataclass(frozen=True)
class FieldSaveErrors:
    unknown_field: str
    missing_system_field: str
    invalid_system_field: str


def allocate_field_key(label: str, used_keys: set[str]) -> str:
    """Build a stable unique ASCII key for a newly added form field."""
    polish_ascii = label.replace("ł", "l").replace("Ł", "L")
    normalized = (
        unicodedata.normalize("NFKD", polish_ascii)
        .encode("ascii", "ignore")
        .decode()
        .lower()
    )
    base = re.sub(r"[^a-z0-9]+", "_", normalized).strip("_") or "pytanie"
    key = base
    suffix = 2
    while key in used_keys:
        key = f"{base}_{suffix}"
        suffix += 1
    used_keys.add(key)
    return key


def save_field_drafts[FieldT: FormFieldEntity, DraftT: FormFieldDraft](
    repo: FormFieldRepository[FieldT],
    drafts: Sequence[DraftT],
    *,
    system_field_is_valid: Callable[[FieldT, DraftT], bool],
    errors: FieldSaveErrors,
) -> list[FieldT]:
    """Replace the editable form definition in one transaction."""
    try:
        current = repo.list_fields()
        by_id = {field.id: field for field in current}
        submitted_ids = {draft.id for draft in drafts if draft.id is not None}
        if submitted_ids - set(by_id):
            raise NotFoundError(errors.unknown_field)

        system_ids = {field.id for field in current if field.is_system}
        if not system_ids.issubset(submitted_ids):
            raise ConflictError(errors.missing_system_field)

        used_keys = {field.key for field in current}
        for position, draft in enumerate(drafts):
            if draft.id is None:
                repo.create_field(
                    FormFieldWrite(
                        key=allocate_field_key(draft.label, used_keys),
                        label=draft.label,
                        field_type=draft.field_type,
                        required=draft.required,
                        placeholder=draft.placeholder,
                        options=draft.options,
                        position=position,
                        is_active=draft.is_active,
                        is_system=False,
                    )
                )
                continue

            field = by_id[draft.id]
            if field.is_system and not system_field_is_valid(field, draft):
                raise ConflictError(errors.invalid_system_field)
            field.label = draft.label
            field.field_type = draft.field_type
            field.required = draft.required
            field.placeholder = draft.placeholder
            field.options = draft.options
            field.position = position
            field.is_active = draft.is_active

        for field in current:
            if field.id not in submitted_ids:
                repo.delete_field(field)

        repo.commit(skip_audit=True)
        return repo.list_fields()
    except Exception:
        repo.rollback()
        raise
