from unittest.mock import MagicMock

from app.core.audit import AuditEntry
from app.modules.audit.models import AuditEvent
from app.modules.audit.services.audit import SqlAuditService


def test_record_adds_event_and_marks_transaction_without_committing() -> None:
    repository = MagicMock()
    service = SqlAuditService(repository)

    service.record(
        AuditEntry(
            entity_type="pi_beneficiary",
            entity_id="42",
            action="UPDATE",
            actor_id="7",
            actor_display_name="admin@example.com",
            context_type="pi_group",
            context_id="3",
            changes={"notes": {"old": "A", "new": "B"}},
        )
    )

    event = repository.add.call_args.args[0]
    assert isinstance(event, AuditEvent)
    assert event.entity_type == "pi_beneficiary"
    assert event.entity_id == "42"
    assert event.changes == {"notes": {"old": "A", "new": "B"}}
    repository.mark_recorded.assert_called_once_with()
    repository.commit.assert_not_called()


def test_reader_delegates_filters_and_pagination() -> None:
    repository = MagicMock()
    repository.get_by_entity.return_value = [MagicMock()]
    service = SqlAuditService(repository)

    result = service.get_logs_for_entity("pi_beneficiary", "42", limit=20, offset=5)

    assert result == repository.get_by_entity.return_value
    repository.get_by_entity.assert_called_once_with(
        entity_type="pi_beneficiary",
        entity_id="42",
        limit=20,
        offset=5,
    )
