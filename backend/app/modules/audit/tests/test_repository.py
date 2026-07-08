from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.modules.audit.models import AuditEvent
from app.modules.audit.repositories.audit import AuditRepository


def _event(
    event_id: int,
    created_at: datetime,
    *,
    entity_id: str = "42",
    context_id: str = "3",
) -> AuditEvent:
    return AuditEvent(
        id=event_id,
        created_at=created_at,
        entity_type="pi_beneficiary",
        entity_id=entity_id,
        action="UPDATE",
        actor_id="7",
        actor_display_name="admin@example.com",
        context_type="pi_group",
        context_id=context_id,
        changes={"notes": {"old": "A", "new": "B"}},
    )


def test_repository_reads_entity_and_context_newest_first(db_session: Session) -> None:
    repository = AuditRepository(db_session)
    now = datetime(2026, 7, 5, tzinfo=UTC)
    db_session.add_all(
        [
            _event(1, now - timedelta(minutes=1)),
            _event(2, now),
            _event(3, now + timedelta(minutes=1), entity_id="99", context_id="8"),
        ]
    )
    db_session.commit()

    by_entity = repository.get_by_entity("pi_beneficiary", "42")
    by_context = repository.get_by_context("pi_group", "3")
    combined = repository.get_by_entity_or_context("pi_group", "3")

    assert [event.id for event in by_entity] == [2, 1]
    assert [event.id for event in by_context] == [2, 1]
    assert [event.id for event in combined] == [2, 1]
