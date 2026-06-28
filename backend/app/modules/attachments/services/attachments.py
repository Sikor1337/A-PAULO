"""Attachment services."""

import hashlib
import logging
import re
from pathlib import Path
from urllib.parse import unquote

from sqlalchemy.orm import Session

from app.core.constants import (
    ATTACHMENT_ALLOWED_CONTENT_TYPES,
    ATTACHMENT_ALLOWED_EXTENSIONS,
    ATTACHMENT_FALLBACK_CONTENT_TYPES,
    ATTACHMENT_SUPPORTED_FILES_MESSAGE,
    BO_CARD_CONTEXT,
)
from app.core.errors import NotFoundError, ValidationException
from app.infrastructure.storage.attachments import AttachmentStorage
from app.modules.attachments.models import Attachment
from app.modules.attachments.repositories import AttachmentRepository
from app.modules.core_data.models import User
from app.modules.pi.repositories import (
    BeneficiaryAssignmentRepository,
    BeneficiaryRepository,
    GroupRepository,
    VolunteerRepository,
)

logger = logging.getLogger(__name__)


class AttachmentService:
    """Business logic for file attachments."""

    def __init__(
        self,
        session: Session,
        storage: AttachmentStorage,
        max_size_bytes: int,
    ):
        self.session = session
        self.storage = storage
        self.max_size_bytes = max_size_bytes
        self.repo = AttachmentRepository(session)
        self.group_repo = GroupRepository(session)
        self.beneficiary_repo = BeneficiaryRepository(session)
        self.volunteer_repo = VolunteerRepository(session)
        self.assignment_repo = BeneficiaryAssignmentRepository(session)

    def list_bo_cards(
        self,
        group_id: int,
        beneficiary_id: int | None = None,
        volunteer_id: int | None = None,
        period: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Attachment]:
        """List BO-card attachments by metadata only."""
        normalized_period = self._normalize_period(period) if period else None
        return self.repo.list_bo_cards(
            group_id=group_id,
            beneficiary_id=beneficiary_id,
            volunteer_id=volunteer_id,
            period=normalized_period,
            skip=skip,
            limit=limit,
        )

    def create_bo_card(
        self,
        *,
        group_id: int,
        beneficiary_id: int,
        volunteer_id: int,
        period: str,
        filename: str,
        content_type: str,
        content: bytes,
        actor: User,
        display_name: str | None = None,
        description: str = "",
    ) -> Attachment:
        """Create a BO-card attachment and store the binary file."""
        original_filename = self._normalize_filename(filename)
        normalized_content_type = self._normalize_content_type(content_type)
        normalized_period = self._normalize_period(period)
        self._validate_file(original_filename, normalized_content_type, content)
        self._validate_bo_card_scope(group_id, beneficiary_id, volunteer_id)

        stored = self.storage.save(content, original_filename, BO_CARD_CONTEXT)
        try:
            attachment = self.repo.create(
                context=BO_CARD_CONTEXT,
                group_id=group_id,
                beneficiary_id=beneficiary_id,
                volunteer_id=volunteer_id,
                period=normalized_period,
                display_name=self._normalize_display_name(
                    display_name or original_filename
                ),
                description=(description or "").strip(),
                original_filename=original_filename,
                storage_backend=stored.storage_backend,
                storage_key=stored.storage_key,
                content_type=normalized_content_type,
                size_bytes=len(content),
                checksum_sha256=hashlib.sha256(content).hexdigest(),
                created_by_id=actor.id,
                created_by_username=actor.username,
                updated_by_id=actor.id,
                updated_by_username=actor.username,
            )
            self.session.flush()
            self.session.refresh(attachment)
            self.session.commit()
            return attachment
        except Exception:
            self.session.rollback()
            try:
                self.storage.delete(stored.storage_key)
            except Exception:
                logger.exception(
                    "Failed to clean up attachment after metadata creation error: %s",
                    stored.storage_key,
                )
            raise

    def get_attachment_by_id(self, attachment_id: int) -> Attachment:
        """Get attachment metadata or raise NotFoundError."""
        attachment = self.repo.get_by_id(attachment_id)
        if not attachment:
            raise NotFoundError(f"Attachment with ID {attachment_id} not found")
        return attachment

    def get_file_path(self, attachment_id: int) -> tuple[Attachment, Path]:
        """Return metadata and local path for downloading/viewing."""
        attachment = self.get_attachment_by_id(attachment_id)
        return attachment, self.storage.get_path(attachment.storage_key)

    def update_attachment(
        self,
        attachment_id: int,
        *,
        actor: User,
        display_name: str | None = None,
        description: str | None = None,
    ) -> Attachment:
        """Update editable attachment metadata."""
        try:
            attachment = self.get_attachment_by_id(attachment_id)
            patch = {
                "updated_by_id": actor.id,
                "updated_by_username": actor.username,
            }
            if display_name is not None:
                patch["display_name"] = self._normalize_display_name(display_name)
            if description is not None:
                patch["description"] = description.strip()
            attachment = self.repo.update(attachment, **patch)
            self.session.flush()
            self.session.refresh(attachment)
            self.session.commit()
            return attachment
        except Exception:
            self.session.rollback()
            raise

    def delete_attachment(self, attachment_id: int) -> None:
        """Delete metadata and file, restoring the file if the DB commit fails."""
        attachment = self.get_attachment_by_id(attachment_id)
        storage_key = attachment.storage_key
        backup: bytes | None
        try:
            backup = self.storage.read(storage_key)
        except NotFoundError:
            backup = None

        if backup is not None:
            self.storage.delete(storage_key)

        try:
            self.repo.delete(attachment)
            self.session.commit()
        except Exception:
            self.session.rollback()
            if backup is not None:
                try:
                    self.storage.restore(storage_key, backup)
                except Exception:
                    logger.exception(
                        "Failed to restore attachment after metadata "
                        "deletion error: %s",
                        storage_key,
                    )
            raise

    def _validate_bo_card_scope(
        self,
        group_id: int,
        beneficiary_id: int,
        volunteer_id: int,
    ) -> None:
        group = self.group_repo.get_by_id(group_id)
        if not group:
            raise NotFoundError(f"Group with ID {group_id} not found")

        beneficiary = self.beneficiary_repo.get_by_id(beneficiary_id)
        if not beneficiary:
            raise NotFoundError(f"Beneficiary with ID {beneficiary_id} not found")
        if beneficiary.group_id != group_id:
            raise ValidationException("Beneficiary does not belong to the group")

        volunteer = self.volunteer_repo.get_by_id(volunteer_id)
        if not volunteer:
            raise NotFoundError(f"Volunteer with ID {volunteer_id} not found")

        assignment = self.assignment_repo.get_by_beneficiary_volunteer(
            beneficiary_id,
            volunteer_id,
        )
        if not assignment:
            raise ValidationException("Volunteer is not assigned to this beneficiary")

    def _validate_file(
        self,
        filename: str,
        content_type: str,
        content: bytes,
    ) -> None:
        if not content:
            raise ValidationException("Attachment file cannot be empty")
        if len(content) > self.max_size_bytes:
            raise ValidationException("Attachment file is too large")

        extension = Path(filename).suffix.lower()
        if extension not in ATTACHMENT_ALLOWED_EXTENSIONS:
            raise ValidationException(ATTACHMENT_SUPPORTED_FILES_MESSAGE)
        if (
            content_type not in ATTACHMENT_ALLOWED_CONTENT_TYPES
            and content_type not in ATTACHMENT_FALLBACK_CONTENT_TYPES
        ):
            raise ValidationException(ATTACHMENT_SUPPORTED_FILES_MESSAGE)

    @staticmethod
    def _normalize_content_type(content_type: str) -> str:
        return (content_type or "application/octet-stream").split(";", 1)[0].strip()

    @staticmethod
    def _normalize_filename(filename: str) -> str:
        decoded = unquote(filename or "").strip()
        name = Path(decoded).name
        if not name or name in {".", ".."}:
            raise ValidationException("Attachment filename is required")
        return name[:255]

    @staticmethod
    def _normalize_display_name(display_name: str) -> str:
        normalized = display_name.strip()
        if not normalized:
            raise ValidationException("Attachment display name is required")
        return normalized[:255]

    @staticmethod
    def _normalize_period(period: str) -> str:
        match = re.fullmatch(r"(\d{4})-(0?[1-9]|1[0-2])", period.strip())
        if not match:
            raise ValidationException("Period must use YYYY-MM format")
        year, month = match.groups()
        return f"{year}-{int(month):02d}"
