"""Attachment services."""

import hashlib
import logging
import re
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path
from tempfile import SpooledTemporaryFile
from typing import BinaryIO, cast
from urllib.parse import unquote
from zipfile import ZIP_DEFLATED, ZipFile

from sqlalchemy.orm import Session

from app.core.constants import (
    ATTACHMENT_ALLOWED_CONTENT_TYPES,
    ATTACHMENT_ALLOWED_EXTENSIONS,
    ATTACHMENT_FALLBACK_CONTENT_TYPES,
    ATTACHMENT_SUPPORTED_FILES_MESSAGE,
    BO_CARD_ARCHIVE_MAX_FILES,
    BO_CARD_ARCHIVE_MAX_UNCOMPRESSED_BYTES,
    BO_CARD_ARCHIVE_MEMORY_THRESHOLD_BYTES,
    BO_CARD_CONTEXT,
    BO_CARD_SORT_KEYS,
    BOCardSortKey,
    SortDirection,
)
from app.core.errors import NotFoundError, ValidationException
from app.infrastructure.storage.attachments import AttachmentStorage
from app.modules.attachments.models import Attachment
from app.modules.attachments.repositories import (
    AttachmentRepository,
    BOCardOverviewRow,
)
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
        *,
        group_id: int | None = None,
        beneficiary_id: int | None = None,
        volunteer_id: int | None = None,
        period: str | None = None,
        period_from: str | None = None,
        period_to: str | None = None,
        search: str | None = None,
        has_comment: bool | None = None,
        sort_by: str = "created_at",
        sort_direction: str = "desc",
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[dict], int]:
        """List BO-card metadata across all or selected groups."""
        normalized_period = self._normalize_period(period) if period else None
        normalized_from, normalized_to = self._normalize_period_range(
            period_from,
            period_to,
        )
        normalized_sort_by = self._normalize_sort_by(sort_by)
        normalized_direction = self._normalize_sort_direction(sort_direction)
        rows, total = self.repo.list_bo_cards_overview(
            group_id=group_id,
            beneficiary_id=beneficiary_id,
            volunteer_id=volunteer_id,
            period=normalized_period,
            period_from=normalized_from,
            period_to=normalized_to,
            search=self._normalize_search(search),
            has_comment=has_comment,
            sort_by=normalized_sort_by,
            sort_direction=normalized_direction,
            skip=skip,
            limit=limit,
        )
        return [self._serialize_overview_row(row) for row in rows], total

    def build_bo_cards_archive(
        self,
        *,
        group_id: int | None = None,
        beneficiary_id: int | None = None,
        volunteer_id: int | None = None,
        period: str | None = None,
        period_from: str | None = None,
        period_to: str | None = None,
        search: str | None = None,
        has_comment: bool | None = None,
    ) -> tuple[BinaryIO, int]:
        """Build a bounded, disk-spooled ZIP archive for matching BO cards."""
        normalized_period = self._normalize_period(period) if period else None
        normalized_from, normalized_to = self._normalize_period_range(
            period_from,
            period_to,
        )
        rows = self.repo.list_bo_cards_for_archive(
            group_id=group_id,
            beneficiary_id=beneficiary_id,
            volunteer_id=volunteer_id,
            period=normalized_period,
            period_from=normalized_from,
            period_to=normalized_to,
            search=self._normalize_search(search),
            has_comment=has_comment,
        )
        return self._create_bo_cards_archive(rows)

    def _create_bo_cards_archive(
        self,
        rows: Iterable[BOCardOverviewRow],
    ) -> tuple[BinaryIO, int]:
        """Write rows to a bounded spooled ZIP and count included files."""
        archive_file: BinaryIO = SpooledTemporaryFile(  # noqa: SIM115
            max_size=BO_CARD_ARCHIVE_MEMORY_THRESHOLD_BYTES,
            mode="w+b",
        )
        used_names: set[str] = set()
        included_count = 0
        total_size = 0
        try:
            with ZipFile(archive_file, "w", ZIP_DEFLATED) as archive:
                for row in rows:
                    attachment, group_name, beneficiary_name, volunteer_name = row
                    try:
                        path = self.storage.get_path(attachment.storage_key)
                    except NotFoundError:
                        logger.warning(
                            "Skipping missing attachment in BO-card archive: %s",
                            attachment.storage_key,
                        )
                        continue

                    if included_count >= BO_CARD_ARCHIVE_MAX_FILES:
                        raise ValidationException(
                            "Too many files selected for one BO-card archive"
                        )
                    total_size += attachment.size_bytes
                    if total_size > BO_CARD_ARCHIVE_MAX_UNCOMPRESSED_BYTES:
                        raise ValidationException(
                            "BO-card archive selection is too large"
                        )

                    archive_name = self._build_archive_name(
                        attachment=attachment,
                        group_name=group_name,
                        beneficiary_name=beneficiary_name,
                        volunteer_name=volunteer_name,
                        used_names=used_names,
                    )
                    archive.write(path, archive_name)
                    included_count += 1

            archive_file.seek(0)
            return archive_file, included_count
        except Exception:
            archive_file.close()
            raise

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

    def _normalize_period_range(
        self,
        period_from: str | None,
        period_to: str | None,
    ) -> tuple[str | None, str | None]:
        normalized_from = self._normalize_period(period_from) if period_from else None
        normalized_to = self._normalize_period(period_to) if period_to else None
        if normalized_from and normalized_to and normalized_from > normalized_to:
            raise ValidationException("Period from cannot be later than period to")
        return normalized_from, normalized_to

    @staticmethod
    def _normalize_search(search: str | None) -> str | None:
        normalized = (search or "").strip()
        return normalized or None

    @staticmethod
    def _normalize_sort_by(sort_by: str) -> BOCardSortKey:
        if sort_by not in BO_CARD_SORT_KEYS:
            raise ValidationException("Unsupported sort field")
        return cast(BOCardSortKey, sort_by)

    @staticmethod
    def _normalize_sort_direction(sort_direction: str) -> SortDirection:
        normalized = sort_direction.lower().strip()
        if normalized not in {"asc", "desc"}:
            raise ValidationException("Sort direction must be asc or desc")
        return cast(SortDirection, normalized)

    @staticmethod
    def _serialize_overview_row(row: BOCardOverviewRow) -> dict:
        attachment, group_name, beneficiary_name, volunteer_name = row
        return {
            "id": attachment.id,
            "context": attachment.context,
            "group_id": attachment.group_id,
            "beneficiary_id": attachment.beneficiary_id,
            "volunteer_id": attachment.volunteer_id,
            "period": attachment.period,
            "display_name": attachment.display_name,
            "description": attachment.description,
            "original_filename": attachment.original_filename,
            "storage_backend": attachment.storage_backend,
            "content_type": attachment.content_type,
            "size_bytes": attachment.size_bytes,
            "checksum_sha256": attachment.checksum_sha256,
            "created_by_id": attachment.created_by_id,
            "created_by_username": attachment.created_by_username,
            "updated_by_id": attachment.updated_by_id,
            "updated_by_username": attachment.updated_by_username,
            "created_at": attachment.created_at,
            "updated_at": attachment.updated_at,
            "group_name": group_name,
            "beneficiary_name": beneficiary_name,
            "volunteer_name": volunteer_name,
        }

    def _build_archive_name(
        self,
        *,
        attachment: Attachment,
        group_name: str | None,
        beneficiary_name: str | None,
        volunteer_name: str | None,
        used_names: set[str],
    ) -> str:
        filename = self._archive_filename(attachment)
        parts = [
            self._safe_archive_segment(attachment.period, "bez-okresu"),
            self._safe_archive_segment(group_name, "bez-grupy"),
            self._safe_archive_segment(beneficiary_name, "bez-podopiecznego"),
            self._safe_archive_segment(volunteer_name, "bez-wolontariusza"),
            filename,
        ]
        archive_name = "/".join(parts)
        if archive_name not in used_names:
            used_names.add(archive_name)
            return archive_name

        stem = Path(filename).stem
        suffix = Path(filename).suffix
        index = 2
        while True:
            candidate = "/".join([*parts[:-1], f"{stem} ({index}){suffix}"])
            if candidate not in used_names:
                used_names.add(candidate)
                return candidate
            index += 1

    def _archive_filename(self, attachment: Attachment) -> str:
        display_name = self._safe_archive_segment(
            attachment.display_name,
            attachment.original_filename,
            max_length=160,
        )
        original_suffix = Path(attachment.original_filename).suffix
        if original_suffix and not Path(display_name).suffix:
            display_name = f"{display_name}{original_suffix}"
        return display_name

    @staticmethod
    def _safe_archive_segment(
        value: str | None,
        fallback: str,
        *,
        max_length: int = 80,
    ) -> str:
        text = (value or fallback).strip() or fallback
        safe = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "_", text)
        safe = re.sub(r"\s+", " ", safe).strip(" .")
        return (safe or fallback)[:max_length]

    @staticmethod
    def archive_filename() -> str:
        """Return a stable ASCII filename for a BO-card archive."""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        return f"karty-bo-{timestamp}.zip"
