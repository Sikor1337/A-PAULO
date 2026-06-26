"""Attachment repositories."""

from sqlalchemy.orm import Session

from app.modules.attachments.models import Attachment


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

