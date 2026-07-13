"""Shared persistence rules for configurable recruitment form fields."""

import re
import unicodedata
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Protocol

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


def ensure_default_fields[FieldT: FormFieldEntity](
    repo: FormFieldRepository[FieldT],
    defaults: Sequence[Mapping[str, Any]],
) -> None:
    """Create missing defaults and restore invariants of protected fields."""
    try:
        current = repo.list_fields()
        defaults_to_ensure = (
            defaults
            if not current
            else [values for values in defaults if values.get("is_system")]
        )
        by_key = {field.key: field for field in current}
        changed = False

        for values in defaults_to_ensure:
            key = str(values["key"])
            field = by_key.get(key)
            if field is None:
                field = repo.create_field(
                    FormFieldWrite(
                        key=key,
                        label=str(values["label"]),
                        field_type=str(values["field_type"]),
                        required=bool(values["required"]),
                        placeholder=str(values.get("placeholder", "")),
                        options=[],
                        position=0,
                        is_active=True,
                        is_system=bool(values.get("is_system", False)),
                    )
                )
                by_key[key] = field
                changed = True
                continue

            if values.get("is_system"):
                expected_type = str(values["field_type"])
                expected_required = bool(values["required"])
                if field.field_type != expected_type:
                    field.field_type = expected_type
                    changed = True
                if field.required != expected_required:
                    field.required = expected_required
                    changed = True
                if not field.is_active:
                    field.is_active = True
                    changed = True
                if not field.is_system:
                    field.is_system = True
                    changed = True

        system_keys = [
            str(values["key"]) for values in defaults if values.get("is_system")
        ]
        ordered = [by_key[key] for key in system_keys]
        if current:
            ordered.extend(field for field in current if field.key not in system_keys)
        else:
            ordered.extend(
                by_key[str(values["key"])]
                for values in defaults
                if not values.get("is_system")
            )
        for position, field in enumerate(ordered):
            if field.position != position:
                field.position = position
                changed = True

        if changed:
            repo.commit(skip_audit=True)
    except Exception:
        repo.rollback()
        raise


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
