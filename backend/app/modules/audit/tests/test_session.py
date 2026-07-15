from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.infrastructure.sql.factory import AuditAwareSession, SQLConnectionFactory
from app.modules.audit.exceptions import MissingAuditRecordError
from app.modules.audit.models import AuditEvent
from app.modules.audit.repositories.audit import AuditRepository


@pytest.fixture
def guarded_session():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    with engine.begin() as connection:
        connection.exec_driver_sql(
            "CREATE TABLE business_items (id INTEGER PRIMARY KEY, value TEXT)"
        )
    AuditEvent.__table__.create(engine)
    factory = sessionmaker(
        bind=engine,
        class_=AuditAwareSession,
        expire_on_commit=False,
    )
    session = factory()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


def _event(event_id: int = 1) -> AuditEvent:
    return AuditEvent(
        id=event_id,
        created_at=datetime(2026, 7, 5, tzinfo=UTC),
        entity_type="pi_beneficiary",
        entity_id="42",
        action="UPDATE",
        actor_id="7",
        actor_display_name="admin@example.com",
        changes={"notes": {"old": "A", "new": "B"}},
    )


def test_sql_factory_uses_guarded_sessions() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    factory = SQLConnectionFactory().create_session_factory(
        engine, use_scoped_session=False
    )
    session = factory()
    try:
        assert isinstance(session, AuditAwareSession)
    finally:
        session.close()
        engine.dispose()


def test_commit_without_audit_is_blocked(guarded_session: AuditAwareSession) -> None:
    guarded_session.execute(
        text("INSERT INTO business_items (id, value) VALUES (1, 'change')")
    )

    with pytest.raises(MissingAuditRecordError):
        guarded_session.commit()

    guarded_session.rollback()
    count = guarded_session.execute(
        text("SELECT COUNT(*) FROM business_items")
    ).scalar()
    assert count == 0


def test_explicit_unaudited_commit_is_allowed(
    guarded_session: AuditAwareSession,
) -> None:
    guarded_session.execute(
        text("INSERT INTO business_items (id, value) VALUES (1, 'seed')")
    )

    guarded_session.commit(skip_audit=True)

    count = guarded_session.execute(
        text("SELECT COUNT(*) FROM business_items")
    ).scalar()
    assert count == 1


def test_business_change_and_audit_event_roll_back_together(
    guarded_session: AuditAwareSession,
) -> None:
    repository = AuditRepository(guarded_session)
    guarded_session.execute(
        text("INSERT INTO business_items (id, value) VALUES (1, 'change')")
    )
    repository.add(_event())
    repository.mark_recorded()

    guarded_session.rollback()

    business_count = guarded_session.execute(
        text("SELECT COUNT(*) FROM business_items")
    ).scalar()
    audit_count = guarded_session.query(AuditEvent).count()
    assert business_count == 0
    assert audit_count == 0
    assert "audit_recorded" not in guarded_session.info


def test_business_change_and_audit_event_commit_together(
    guarded_session: AuditAwareSession,
) -> None:
    repository = AuditRepository(guarded_session)
    guarded_session.execute(
        text("INSERT INTO business_items (id, value) VALUES (1, 'change')")
    )
    repository.add(_event())
    repository.mark_recorded()

    guarded_session.commit()

    business_count = guarded_session.execute(
        text("SELECT COUNT(*) FROM business_items")
    ).scalar()
    assert business_count == 1
    assert guarded_session.query(AuditEvent).count() == 1


def test_audit_marker_is_consumed_after_commit(
    guarded_session: AuditAwareSession,
) -> None:
    repository = AuditRepository(guarded_session)
    repository.add(_event())
    repository.mark_recorded()

    guarded_session.commit()

    assert guarded_session.query(AuditEvent).count() == 1
    assert "audit_recorded" not in guarded_session.info
    with pytest.raises(MissingAuditRecordError):
        guarded_session.commit()


def test_persisted_audit_event_cannot_be_updated(
    guarded_session: AuditAwareSession,
) -> None:
    repository = AuditRepository(guarded_session)
    event = _event()
    repository.add(event)
    repository.mark_recorded()
    guarded_session.commit()

    event.action = "TAMPERED"
    repository.mark_recorded()
    with pytest.raises(RuntimeError, match="append-only"):
        guarded_session.commit()
    guarded_session.rollback()


def test_persisted_audit_event_cannot_be_deleted(
    guarded_session: AuditAwareSession,
) -> None:
    repository = AuditRepository(guarded_session)
    event = _event()
    repository.add(event)
    repository.mark_recorded()
    guarded_session.commit()

    guarded_session.delete(event)
    repository.mark_recorded()
    with pytest.raises(RuntimeError, match="append-only"):
        guarded_session.commit()
    guarded_session.rollback()
