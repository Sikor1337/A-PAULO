"""Business rules for public beneficiary recruitment (PAP-90)."""

from datetime import UTC, datetime
from typing import Any

from app.core.errors import ConflictError, NotFoundError, ValidationException
from app.modules.core_data.models import User
from app.modules.pi.schemas.beneficiaries import BeneficiaryCreateRequest
from app.modules.pi.services.beneficiaries import BeneficiaryService
from app.modules.recruitment.beneficiary_access import (
    create_form_token,
    is_valid_form_token,
)
from app.modules.recruitment.models import BeneficiaryRecruitmentField
from app.modules.recruitment.repositories.beneficiary_recruitment import (
    BeneficiaryRecruitmentRepository,
)
from app.modules.recruitment.schemas.beneficiary_recruitment import (
    BeneficiaryRecruitmentSubmissionCreate,
    BeneficiaryRecruitmentSubmissionWrite,
)
from app.modules.recruitment.schemas.recruitment import (
    RecruitmentFieldDraft,
    RecruitmentSubmissionCreate,
)
from app.modules.recruitment.services.form_fields import (
    ConfigurableFormFieldService,
    FieldSaveErrors,
    save_field_drafts,
)


class BeneficiaryRecruitmentService(
    ConfigurableFormFieldService,
        RecruitmentFieldDraft
):
    def __init__(
        self,
        repo: BeneficiaryRecruitmentRepository,
        beneficiaries: BeneficiaryService,
    ):
        self.repo = repo
        self.beneficiaries = beneficiaries
        super().__init__(
            repo,
            system_field_is_valid=lambda field, draft: (
                draft.field_type == field.field_type
                and draft.required == field.required
                and draft.is_active
            ),
            errors=FieldSaveErrors(
                unknown_field="Co najmniej jedno pole formularza nie istnieje",
                missing_system_field="Nie można usunąć podstawowego pola formularza",
                invalid_system_field=(
                    "Podstawowe pola muszą pozostać aktywne w wymaganej postaci"
                ),
            ),
        )

    def list_fields(self, *, active_only: bool = False):
        return self.repo.list_fields(active_only=active_only)

    def save_fields(self, drafts: list[RecruitmentFieldDraft]):
        return save_field_drafts(
            self.repo,
            drafts,
            system_field_is_valid=lambda field, draft: (
                draft.field_type == field.field_type
                and draft.required == field.required
                and draft.is_active
            ),
            errors=FieldSaveErrors(
                unknown_field="Co najmniej jedno pole formularza nie istnieje",
                missing_system_field="Nie można usunąć podstawowego pola formularza",
                invalid_system_field=(
                    "Podstawowe pola muszą pozostać aktywne w wymaganej postaci"
                ),
            ),
        )

    def get_public_form(self) -> dict:
        return {
            "fields": self.list_fields(active_only=True),
            "form_token": create_form_token(),
        }

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
            ).validated_answers(fields)
            values: dict[str, Any] = {
                answer["key"]: answer["value"] for answer in answers
            }
            self._validate_system_lengths(values)
            submission = self.repo.create_submission(
                BeneficiaryRecruitmentSubmissionWrite(
                    full_name=values["full_name"],
                    address=values["address"],
                    phone=values.get("phone") or None,
                    reporter_name=values["reporter_name"],
                    reporter_phone=values["reporter_phone"],
                    help_needed=values["help_needed"],
                    answers=answers,
                )
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
                BeneficiaryCreateRequest(
                    full_name=submission.full_name,
                    address=submission.address,
                    phone=submission.phone,
                    family_phone=submission.reporter_phone,
                    description=submission.help_needed,
                    group=group_id,
                    history=(
                        f"Utworzono ze zgłoszenia rekrutacyjnego #{submission.id}. "
                        f"Osoba zgłaszająca: {submission.reporter_name}."
                    ),
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
