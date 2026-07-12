"""Business rules for public beneficiary recruitment (PAP-90)."""

import re
import unicodedata
from datetime import UTC, datetime
from typing import Any

from app.core.errors import ConflictError, NotFoundError, ValidationException
from app.modules.core_data.models import User
from app.modules.pi.services.beneficiaries import BeneficiaryService
from app.modules.recruitment.beneficiary_access import (
    create_form_token,
    is_valid_form_token,
)
from app.modules.recruitment.beneficiary_constants import BENEFICIARY_DEFAULT_FIELDS
from app.modules.recruitment.repositories.beneficiary_recruitment import (
    BeneficiaryRecruitmentRepository,
)
from app.modules.recruitment.schemas.beneficiary_recruitment import (
    BeneficiaryRecruitmentSubmissionCreate,
)
from app.modules.recruitment.schemas.recruitment import (
    RecruitmentFieldDraft,
    RecruitmentSubmissionCreate,
)


def _slugify(value: str) -> str:
    normalized = (
        unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode().lower()
    )
    return re.sub(r"[^a-z0-9]+", "_", normalized).strip("_") or "pytanie"


class BeneficiaryRecruitmentService:
    def __init__(
        self,
        repo: BeneficiaryRecruitmentRepository,
        beneficiaries: BeneficiaryService,
    ):
        self.repo = repo
        self.beneficiaries = beneficiaries

    def _ensure_default_fields(self) -> None:
        current = self.repo.list_fields()
        by_key = {field.key: field for field in current}
        changed = False
        for position, values in enumerate(BENEFICIARY_DEFAULT_FIELDS):
            field = by_key.get(values["key"])
            if field is None:
                self.repo.create_field(
                    position=position, options=[], is_active=True, **values
                )
                changed = True
                continue
            protected = {
                "field_type": values["field_type"],
                "required": values["required"],
                "is_active": True,
                "is_system": True,
            }
            for attribute, expected in protected.items():
                if getattr(field, attribute) != expected:
                    setattr(field, attribute, expected)
                    changed = True
        if changed:
            self.repo.commit(skip_audit=True)

    def list_fields(self, *, active_only: bool = False):
        self._ensure_default_fields()
        return self.repo.list_fields(active_only=active_only)

    def get_public_form(self) -> dict:
        return {
            "fields": self.list_fields(active_only=True),
            "form_token": create_form_token(),
        }

    def save_fields(self, drafts: list[RecruitmentFieldDraft]):
        try:
            current = self.list_fields()
            by_id = {field.id: field for field in current}
            submitted_ids = {draft.id for draft in drafts if draft.id is not None}
            if submitted_ids - set(by_id):
                raise NotFoundError("Co najmniej jedno pole formularza nie istnieje")
            system_ids = {field.id for field in current if field.is_system}
            if not system_ids.issubset(submitted_ids):
                raise ConflictError("Nie można usunąć podstawowego pola formularza")
            used_keys = {field.key for field in current}
            for position, draft in enumerate(drafts):
                if draft.id is None:
                    base_key = _slugify(draft.label)
                    key, suffix = base_key, 2
                    while key in used_keys:
                        key, suffix = f"{base_key}_{suffix}", suffix + 1
                    used_keys.add(key)
                    self.repo.create_field(
                        key=key,
                        label=draft.label,
                        field_type=draft.field_type,
                        required=draft.required,
                        placeholder=draft.placeholder,
                        options=draft.options,
                        position=position,
                        is_active=draft.is_active,
                        is_system=False,
                    )
                    continue
                field = by_id[draft.id]
                if field.is_system and (
                    draft.field_type != field.field_type
                    or draft.required != field.required
                    or not draft.is_active
                ):
                    raise ConflictError(
                        "Podstawowe pola muszą pozostać aktywne w wymaganej postaci"
                    )
                field.label = draft.label
                field.field_type = draft.field_type
                field.required = draft.required
                field.placeholder = draft.placeholder
                field.options = draft.options
                field.position = position
                field.is_active = draft.is_active
            for field in current:
                if field.id not in submitted_ids:
                    self.repo.delete_field(field)
            self.repo.commit(skip_audit=True)
            return self.repo.list_fields()
        except Exception:
            self.repo.rollback()
            raise

    def submit(self, request: BeneficiaryRecruitmentSubmissionCreate):
        if request.website:
            raise ValidationException("Nie udało się wysłać formularza")
        if not is_valid_form_token(request.form_token):
            raise ValidationException(
                "Formularz wygasł. Odśwież stronę i spróbuj ponownie."
            )
        try:
            fields = self.list_fields(active_only=True)
            answers = RecruitmentSubmissionCreate(
                answers=request.answers
            ).validated_answers(fields)  # type: ignore[arg-type]
            values: dict[str, Any] = {
                answer["key"]: answer["value"] for answer in answers
            }
            self._validate_system_lengths(values)
            submission = self.repo.create_submission(
                full_name=values["full_name"],
                address=values["address"],
                phone=values.get("phone") or None,
                reporter_name=values["reporter_name"],
                reporter_phone=values["reporter_phone"],
                help_needed=values["help_needed"],
                answers=answers,
            )
            self.repo.commit(skip_audit=True)
            self.repo.refresh(submission)
            return submission
        except Exception:
            self.repo.rollback()
            raise

    @staticmethod
    def _validate_system_lengths(values: dict[str, Any]) -> None:
        limits = {
            "full_name": 200,
            "address": 500,
            "phone": 20,
            "reporter_name": 200,
            "reporter_phone": 20,
            "help_needed": 10_000,
        }
        for key, maximum in limits.items():
            value = values.get(key)
            if isinstance(value, str) and len(value) > maximum:
                raise ValidationException("Jedna z odpowiedzi jest zbyt długa")

    def list_submissions(
        self,
        include_archived: bool = False,
        skip: int = 0,
        limit: int = 100,
    ):
        return self.repo.list_submissions(
            include_archived=include_archived,
            skip=skip,
            limit=limit,
        )

    def get_submission(self, submission_id: int):
        submission = self.repo.get_submission(submission_id)
        if not submission:
            raise NotFoundError("Zgłoszenie nie istnieje")
        return submission

    def create_beneficiary(
        self, submission_id: int, actor: User, group_id: int | None = None
    ):
        try:
            submission = self.repo.get_submission_for_update(submission_id)
            if not submission:
                raise NotFoundError("Zgłoszenie nie istnieje")
            if submission.beneficiary_id or submission.status == "BENEFICIARY_CREATED":
                raise ConflictError(
                    "Podopieczny został już utworzony z tego zgłoszenia"
                )
            if submission.status in {"REJECTED", "ARCHIVED"}:
                raise ConflictError(
                    "Nie można wdrożyć odrzuconego lub archiwalnego zgłoszenia"
                )
            beneficiary = self.beneficiaries.prepare_beneficiary(
                actor,
                full_name=submission.full_name,
                address=submission.address,
                phone=submission.phone,
                family_phone=submission.reporter_phone,
                description=submission.help_needed,
                group_id=group_id,
                history=(
                    f"Utworzono ze zgłoszenia rekrutacyjnego #{submission.id}. "
                    f"Osoba zgłaszająca: {submission.reporter_name}."
                ),
            )
            submission.beneficiary_id = beneficiary.id
            submission.status = "BENEFICIARY_CREATED"
            self.repo.commit()
            self.repo.refresh(submission)
            return submission
        except Exception:
            self.repo.rollback()
            raise

    def reject(self, submission_id: int, comment: str | None):
        submission = self.get_submission(submission_id)
        if submission.status == "BENEFICIARY_CREATED":
            raise ConflictError("Wdrożonego zgłoszenia nie można odrzucić")
        submission.status = "REJECTED"
        submission.decision_comment = comment
        self.repo.commit(skip_audit=True)
        self.repo.refresh(submission)
        return submission

    def archive(self, submission_id: int):
        submission = self.get_submission(submission_id)
        if submission.status == "NEW":
            raise ConflictError("Najpierw utwórz podopiecznego albo odrzuć zgłoszenie")
        submission.status = "ARCHIVED"
        submission.archived_at = datetime.now(UTC)
        self.repo.commit(skip_audit=True)
        self.repo.refresh(submission)
        return submission

    def delete(self, submission_id: int) -> None:
        submission = self.get_submission(submission_id)
        if submission.status == "NEW":
            raise ConflictError("Nowe zgłoszenie należy najpierw rozpatrzyć")
        self.repo.delete_submission(submission)
        self.repo.commit(skip_audit=True)
