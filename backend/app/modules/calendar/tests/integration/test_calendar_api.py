from urllib.parse import urlparse

from sqlalchemy.orm import Session

from app.modules.calendar.models import CalendarFeedToken
from app.modules.core_data.models import User


def _persist_admin(session: Session, admin_user: User) -> None:
    session.add(admin_user)
    session.commit()


def _event_payload(**overrides):
    payload = {
        "title": "Świąteczne spotkanie",
        "description": "Opis widoczny tylko w A-PAULO",
        "starts_at": "2026-10-24T18:00:00+02:00",
        "ends_at": "2026-10-24T20:00:00+02:00",
        "timezone": "Europe/Warsaw",
        "is_all_day": False,
        "location": "Biuro A-PAULO",
        "recurrence_rule": "FREQ=WEEKLY;COUNT=3",
        "status": "published",
        "visibility": "organization",
    }
    payload.update(overrides)
    return payload


def test_event_crud_updates_sequence_and_audit(
    api_client,
    db_session: Session,
    admin_user: User,
) -> None:
    _persist_admin(db_session, admin_user)

    created = api_client.post("/api/v1/calendar/events", json=_event_payload())
    assert created.status_code == 201
    event = created.json()
    assert event["sequence"] == 0
    assert event["author_name"] == "Admin User"

    updated = api_client.patch(
        f"/api/v1/calendar/events/{event['id']}",
        json={"location": "Nowe biuro"},
    )
    assert updated.status_code == 200
    assert updated.json()["sequence"] == 1

    listed = api_client.get(
        "/api/v1/calendar/events",
        params={"status": "published", "sort": "asc"},
    )
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()] == [event["id"]]

    downloaded = api_client.get(f"/api/v1/calendar/events/{event['id']}.ics")
    assert downloaded.status_code == 200
    assert downloaded.headers["content-type"].startswith("text/calendar")
    assert "SUMMARY:Świąteczne spotkanie" in downloaded.text
    assert "RRULE:FREQ=WEEKLY;COUNT=3" in downloaded.text
    assert "Opis widoczny tylko w A-PAULO" not in downloaded.text


def test_private_feed_rotates_hashed_token_and_exports_cancellation(
    api_client,
    db_session: Session,
    admin_user: User,
) -> None:
    _persist_admin(db_session, admin_user)
    event = api_client.post("/api/v1/calendar/events", json=_event_payload()).json()
    api_client.post(
        "/api/v1/calendar/events",
        json=_event_payload(
            title="Dzień wolontariatu",
            starts_at="2026-10-25T00:00:00+02:00",
            ends_at="2026-10-25T00:00:00+02:00",
            is_all_day=True,
            recurrence_rule=None,
        ),
    )

    generated = api_client.post("/api/v1/calendar/feed-token")
    assert generated.status_code == 201
    first_url = generated.json()["feed_url"]
    first_path = urlparse(first_url).path
    plain_token = first_path.rsplit("/", 1)[-1].removesuffix(".ics")
    stored = db_session.query(CalendarFeedToken).one()
    assert stored.token_hash != plain_token
    assert len(stored.token_hash) == 64

    feed = api_client.get(first_path)
    assert feed.status_code == 200
    assert feed.headers["cache-control"] == "private, no-store"
    assert "BEGIN:VCALENDAR" in feed.text
    assert "STATUS:CONFIRMED" in feed.text
    assert "DTSTART;VALUE=DATE:20261025" in feed.text

    cancelled = api_client.post(f"/api/v1/calendar/events/{event['id']}/cancel")
    assert cancelled.status_code == 200
    assert cancelled.json()["sequence"] == 1
    assert "STATUS:CANCELLED" in api_client.get(first_path).text

    rotated = api_client.post("/api/v1/calendar/feed-token")
    assert rotated.status_code == 201
    assert api_client.get(first_path).status_code == 404
    assert api_client.get(urlparse(rotated.json()["feed_url"]).path).status_code == 200


def test_event_schema_rejects_end_before_start(
    api_client, db_session, admin_user
) -> None:
    _persist_admin(db_session, admin_user)

    response = api_client.post(
        "/api/v1/calendar/events",
        json=_event_payload(ends_at="2026-10-24T17:00:00+02:00"),
    )

    assert response.status_code == 422
