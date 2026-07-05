"""Attachment repositories."""

from collections.abc import Iterable

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.constants import BO_CARD_CONTEXT, BOCardSortKey, SortDirection
from app.infrastructure.sql.repository import SQLRepository
from app.modules.attachments.models import Attachment
from app.modules.attachments.schemas import (
    BOCardArchiveQuery,
    BOCardAttachmentListQuery,
)
from app.modules.pi.models.beneficiary import Beneficiary
from app.modules.pi.models.group import Group
from app.modules.pi.models.volunteer import Volunteer

BOCardOverviewRow = tuple[Attachment, str | None, str | None, str | None]


class AttachmentRepository(SQLRepository):
    """Repository for attachment metadata."""

    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, attachment_id: int) -> Attachment | None:
        """Get attachment by ID."""
        return self.session.get(Attachment, attachment_id)

    def list_bo_cards_overview(
        self,
        filters: BOCardAttachmentListQuery,
    ) -> tuple[list[BOCardOverviewRow], int]:
        """List BO-card metadata from all groups with joined display names."""
        query = self._bo_cards_overview_query()
        query = self._apply_bo_card_filters(query, filters)
        total = (
            query.with_entities(func.count(Attachment.id)).order_by(None).scalar() or 0
        )
        ordered_query = query.order_by(
            self._sort_expression(filters.sort_by, filters.sort_direction),
            Attachment.id.desc(),
        )
        return ordered_query.offset(filters.skip).limit(filters.limit).all(), total

    def list_bo_cards_for_archive(
        self,
        filters: BOCardArchiveQuery,
    ) -> Iterable[BOCardOverviewRow]:
        """Stream filtered BO-card rows for archive generation."""
        query = self._bo_cards_overview_query()
        query = self._apply_bo_card_filters(query, filters)
        return query.order_by(
            Attachment.period.desc(),
            func.lower(Group.name).asc(),
            func.lower(Beneficiary.full_name).asc(),
            Attachment.id.desc(),
        ).yield_per(100)

    def create(self, **kwargs) -> Attachment:
        """Create attachment metadata."""
        attachment = Attachment(**kwargs)
        self.session.add(attachment)
        return attachment

    def update(self, attachment: Attachment, **kwargs) -> Attachment:
        """Update editable attachment metadata."""
        for key, value in kwargs.items():
            if hasattr(attachment, key):
                setattr(attachment, key, value)
        return attachment

    def delete(self, attachment: Attachment) -> None:
        """Delete attachment metadata."""
        self.session.delete(attachment)

    def _bo_cards_overview_query(self):
        return (
            self.session.query(
                Attachment,
                Group.name.label("group_name"),
                Beneficiary.full_name.label("beneficiary_name"),
                Volunteer.full_name.label("volunteer_name"),
            )
            .outerjoin(Group, Attachment.group_id == Group.id)
            .outerjoin(Beneficiary, Attachment.beneficiary_id == Beneficiary.id)
            .outerjoin(Volunteer, Attachment.volunteer_id == Volunteer.id)
            .filter(Attachment.context == BO_CARD_CONTEXT)
        )

    def _apply_bo_card_filters(
        self,
        query,
        filters: BOCardArchiveQuery | BOCardAttachmentListQuery,
    ):
        if filters.group_id is not None:
            query = query.filter(Attachment.group_id == filters.group_id)
        if filters.beneficiary_id is not None:
            query = query.filter(Attachment.beneficiary_id == filters.beneficiary_id)
        if filters.volunteer_id is not None:
            query = query.filter(Attachment.volunteer_id == filters.volunteer_id)
        if filters.period is not None:
            query = query.filter(Attachment.period == filters.period)
        if filters.period_from is not None:
            query = query.filter(Attachment.period >= filters.period_from)
        if filters.period_to is not None:
            query = query.filter(Attachment.period <= filters.period_to)
        if filters.has_comment is True:
            query = query.filter(Attachment.description != "")
        elif filters.has_comment is False:
            query = query.filter(Attachment.description == "")
        if filters.search:
            pattern = f"%{filters.search.strip()}%"
            query = query.filter(
                or_(
                    Attachment.display_name.ilike(pattern),
                    Attachment.original_filename.ilike(pattern),
                    Attachment.description.ilike(pattern),
                    Attachment.period.ilike(pattern),
                    Group.name.ilike(pattern),
                    Beneficiary.full_name.ilike(pattern),
                    Volunteer.full_name.ilike(pattern),
                )
            )
        return query

    @staticmethod
    def _sort_expression(sort_by: BOCardSortKey, direction: SortDirection):
        sort_map = {
            "created_at": Attachment.created_at,
            "updated_at": Attachment.updated_at,
            "period": Attachment.period,
            "display_name": func.lower(Attachment.display_name),
            "group_name": func.lower(Group.name),
            "beneficiary_name": func.lower(Beneficiary.full_name),
            "volunteer_name": func.lower(Volunteer.full_name),
            "size_bytes": Attachment.size_bytes,
        }
        expression = sort_map[sort_by]
        return expression.asc() if direction == "asc" else expression.desc()
