"""Attachment repositories."""

from typing import Literal

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.modules.attachments.models import Attachment
from app.modules.pi.models.beneficiary import Beneficiary
from app.modules.pi.models.group import Group
from app.modules.pi.models.volunteer import Volunteer

BOCardSortKey = Literal[
    "created_at",
    "updated_at",
    "period",
    "display_name",
    "group_name",
    "beneficiary_name",
    "volunteer_name",
    "size_bytes",
]
BOCardOverviewRow = tuple[Attachment, str | None, str | None, str | None]


class AttachmentRepository:
    """Repository for attachment metadata."""

    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, attachment_id: int) -> Attachment | None:
        """Get attachment by ID."""
        return (
            self.session.query(Attachment)
            .filter(Attachment.id == attachment_id)
            .first()
        )

    def list_bo_cards(
        self,
        group_id: int,
        beneficiary_id: int | None = None,
        volunteer_id: int | None = None,
        period: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Attachment]:
        """List BO-card attachment metadata for a group."""
        query = self.session.query(Attachment).filter(
            Attachment.context == "bo_card",
            Attachment.group_id == group_id,
        )

        if beneficiary_id is not None:
            query = query.filter(Attachment.beneficiary_id == beneficiary_id)
        if volunteer_id is not None:
            query = query.filter(Attachment.volunteer_id == volunteer_id)
        if period is not None:
            query = query.filter(Attachment.period == period)

        return (
            query.order_by(Attachment.created_at.desc(), Attachment.id.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def list_bo_cards_overview(
        self,
        *,
        group_id: int | None = None,
        beneficiary_id: int | None = None,
        volunteer_id: int | None = None,
        period_from: str | None = None,
        period_to: str | None = None,
        search: str | None = None,
        has_comment: bool | None = None,
        sort_by: BOCardSortKey = "created_at",
        sort_direction: Literal["asc", "desc"] = "desc",
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[BOCardOverviewRow], int]:
        """List BO-card metadata from all groups with joined display names."""
        query = self._bo_cards_overview_query()
        query = self._apply_bo_card_filters(
            query,
            group_id=group_id,
            beneficiary_id=beneficiary_id,
            volunteer_id=volunteer_id,
            period_from=period_from,
            period_to=period_to,
            search=search,
            has_comment=has_comment,
        )
        total = (
            query.with_entities(func.count(Attachment.id)).order_by(None).scalar()
            or 0
        )
        ordered_query = query.order_by(
            self._sort_expression(sort_by, sort_direction),
            Attachment.id.desc(),
        )
        return ordered_query.offset(skip).limit(limit).all(), total

    def list_bo_cards_for_archive(
        self,
        *,
        group_id: int | None = None,
        beneficiary_id: int | None = None,
        volunteer_id: int | None = None,
        period_from: str | None = None,
        period_to: str | None = None,
        search: str | None = None,
        has_comment: bool | None = None,
    ) -> list[BOCardOverviewRow]:
        """List all filtered BO-card rows for archive generation."""
        query = self._bo_cards_overview_query()
        query = self._apply_bo_card_filters(
            query,
            group_id=group_id,
            beneficiary_id=beneficiary_id,
            volunteer_id=volunteer_id,
            period_from=period_from,
            period_to=period_to,
            search=search,
            has_comment=has_comment,
        )
        return query.order_by(
            Attachment.period.desc(),
            func.lower(Group.name).asc(),
            func.lower(Beneficiary.full_name).asc(),
            Attachment.id.desc(),
        ).all()

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
            .filter(Attachment.context == "bo_card")
        )

    def _apply_bo_card_filters(
        self,
        query,
        *,
        group_id: int | None,
        beneficiary_id: int | None,
        volunteer_id: int | None,
        period_from: str | None,
        period_to: str | None,
        search: str | None,
        has_comment: bool | None,
    ):
        if group_id is not None:
            query = query.filter(Attachment.group_id == group_id)
        if beneficiary_id is not None:
            query = query.filter(Attachment.beneficiary_id == beneficiary_id)
        if volunteer_id is not None:
            query = query.filter(Attachment.volunteer_id == volunteer_id)
        if period_from is not None:
            query = query.filter(Attachment.period >= period_from)
        if period_to is not None:
            query = query.filter(Attachment.period <= period_to)
        if has_comment is True:
            query = query.filter(Attachment.description != "")
        elif has_comment is False:
            query = query.filter(Attachment.description == "")
        if search:
            pattern = f"%{search.strip()}%"
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
    def _sort_expression(sort_by: BOCardSortKey, direction: Literal["asc", "desc"]):
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
