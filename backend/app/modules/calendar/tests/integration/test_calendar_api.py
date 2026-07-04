from urllib.parse import urlparse

from sqlalchemy.orm import Session

from app.modules.calendar.models import CalendarFeedToken
from app.modules.core_data.models import User
from app.modules.security.dependencies import get_current_user
from app.modules.security.models import Permission, UserGroup, security_user_groups
from app.modules.security.models.constants import CAN_VIEW_EVENTS


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
) -> None:
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
) -> None:
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
    rotated_path = urlparse(rotated.json()["feed_url"]).path
    assert api_client.get(rotated_path).status_code == 200

    admin_group = db_session.query(UserGroup).filter_by(system_key="admin").one()
    admin_group.permissions = [
        permission
        for permission in admin_group.permissions
        if permission.code != CAN_VIEW_EVENTS
    ]
    db_session.commit()

    assert api_client.get(rotated_path).status_code == 404


def test_event_schema_rejects_end_before_start(api_client) -> None:
    response = api_client.post(
        "/api/v1/calendar/events",
        json=_event_payload(ends_at="2026-10-24T17:00:00+02:00"),
    )

    assert response.status_code == 422


def test_event_schema_rejects_naive_dates_and_malformed_rrule(api_client) -> None:
    naive = api_client.post(
        "/api/v1/calendar/events",
        json=_event_payload(
            starts_at="2026-10-24T18:00:00",
            ends_at="2026-10-24T20:00:00",
        ),
    )
    malformed_rrule = api_client.post(
        "/api/v1/calendar/events",
        json=_event_payload(recurrence_rule="FREQ=WEEKLY;COUNT=2\r\nSUMMARY:Injected"),
    )

    assert naive.status_code == 422
    assert malformed_rrule.status_code == 422


def test_view_permission_filters_private_events_and_does_not_allow_changes(
    api_client,
    db_session: Session,
) -> None:
    organization = api_client.post(
        "/api/v1/calendar/events",
        json=_event_payload(title="Organizacja"),
    ).json()
    private = api_client.post(
        "/api/v1/calendar/events",
        json=_event_payload(title="Zarządzający", visibility="admins"),
    ).json()
    draft = api_client.post(
        "/api/v1/calendar/events",
        json=_event_payload(title="Szkic", status="draft"),
    ).json()
    permission = db_session.query(Permission).filter_by(code=CAN_VIEW_EVENTS).one()
    viewer = User(
        username="calendar-viewer",
        email="calendar-viewer@example.com",
        hashed_password="unused",
        status="regular",
        is_active=True,
    )
    group = UserGroup(name="Calendar viewers", permissions=[permission])
    db_session.add_all([viewer, group])
    db_session.flush()
    db_session.execute(
        security_user_groups.insert(),
        {"user_id": viewer.id, "group_id": group.id},
    )
    db_session.commit()
    api_client.app.dependency_overrides[get_current_user] = lambda: viewer

    listed = api_client.get("/api/v1/calendar/events")
    hidden = api_client.get(f"/api/v1/calendar/events/{private['id']}")
    hidden_draft = api_client.get(f"/api/v1/calendar/events/{draft['id']}")
    create = api_client.post(
        "/api/v1/calendar/events",
        json=_event_payload(title="Niedozwolone"),
    )

    assert listed.status_code == 200
    assert [event["id"] for event in listed.json()] == [organization["id"]]
    assert hidden.status_code == 404
    assert hidden_draft.status_code == 404
    assert create.status_code == 403
