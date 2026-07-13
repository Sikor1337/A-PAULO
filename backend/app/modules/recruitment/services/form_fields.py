"""Shared persistence rules for configurable recruitment form fields."""

import re
import unicodedata
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Protocol, cast

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


class FormFieldRepository[FieldT](Protocol):
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


class ConfigurableFormFieldService[
    FieldT,
    DraftT: FormFieldDraft,
]:
    """Shared field-list and field-editor workflow for configurable forms."""

    def __init__(
        self,
        repo: FormFieldRepository[FieldT],
        *,
        defaults: Sequence[Mapping[str, Any]],
        errors: FieldSaveErrors,
    ) -> None:
        self._form_field_repo = repo
        self._form_field_defaults = defaults
        self._form_field_errors = errors

    def list_fields(self, *, active_only: bool = False) -> list[FieldT]:
        ensure_default_fields(self._form_field_repo, self._form_field_defaults)
        return self._form_field_repo.list_fields(active_only=active_only)

    def save_fields(self, drafts: list[DraftT]) -> list[FieldT]:
        ensure_default_fields(self._form_field_repo, self._form_field_defaults)
        return save_field_drafts(
            self._form_field_repo,
            drafts,
            errors=self._form_field_errors,
        )


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


def _as_form_field(field: object) -> FormFieldEntity:
    """Bridge SQLAlchemy mapped attributes to the structural field contract."""
    return cast(FormFieldEntity, field)


def ensure_default_fields[FieldT](
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
        by_key = {_as_form_field(field).key: field for field in current}
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

            field_data = _as_form_field(field)
            if values.get("is_system"):
                expected_type = str(values["field_type"])
                expected_required = bool(values["required"])
                if field_data.field_type != expected_type:
                    field_data.field_type = expected_type
                    changed = True
                if field_data.required != expected_required:
                    field_data.required = expected_required
                    changed = True
                if not field_data.is_active:
                    field_data.is_active = True
                    changed = True
                if not field_data.is_system:
                    field_data.is_system = True
                    changed = True

        system_keys = [
            str(values["key"]) for values in defaults if values.get("is_system")
        ]
        ordered = [by_key[key] for key in system_keys]
        if current:
            ordered.extend(
                field
                for field in current
                if _as_form_field(field).key not in system_keys
            )
        else:
            ordered.extend(
                by_key[str(values["key"])]
                for values in defaults
                if not values.get("is_system")
            )
        for position, field in enumerate(ordered):
            field_data = _as_form_field(field)
            if field_data.position != position:
                field_data.position = position
                changed = True

        if changed:
            repo.commit(skip_audit=True)
    except Exception:
        repo.rollback()
        raise


def save_field_drafts[FieldT, DraftT: FormFieldDraft](
    repo: FormFieldRepository[FieldT],
    drafts: Sequence[DraftT],
    *,
    errors: FieldSaveErrors,
) -> list[FieldT]:
    """Replace the editable form definition in one transaction."""
    try:
        current = repo.list_fields()
        by_id = {_as_form_field(field).id: field for field in current}
        submitted_ids = {draft.id for draft in drafts if draft.id is not None}
        if submitted_ids - set(by_id):
            raise NotFoundError(errors.unknown_field)

        system_ids = {
            field_data.id
            for field in current
            if (field_data := _as_form_field(field)).is_system
        }
        if not system_ids.issubset(submitted_ids):
            raise ConflictError(errors.missing_system_field)

        used_keys = {_as_form_field(field).key for field in current}
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
            field_data = _as_form_field(field)
            if field_data.is_system and (
                draft.field_type != field_data.field_type
                or draft.required != field_data.required
                or not draft.is_active
            ):
                raise ConflictError(errors.invalid_system_field)
            field_data.label = draft.label
            field_data.field_type = draft.field_type
            field_data.required = draft.required
            field_data.placeholder = draft.placeholder
            field_data.options = draft.options
            field_data.position = position
            field_data.is_active = draft.is_active

        for field in current:
            if _as_form_field(field).id not in submitted_ids:
                repo.delete_field(field)

        repo.commit(skip_audit=True)
        return repo.list_fields()
    except Exception:
        repo.rollback()
        raise
