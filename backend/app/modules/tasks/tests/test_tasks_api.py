"""Integration tests for the tasks module (PAP-89)."""

from datetime import UTC, datetime

from app.modules.calendar.models import CalendarEvent


def _create_department(api_client, name: str = "Remonty") -> dict:
    response = api_client.post(
        "/api/v1/departments", json={"name": name, "icon": "🔨"}
    )
    assert response.status_code == 200
    return response.json()


def _create_volunteer(api_client, email: str) -> dict:
    response = api_client.post(
        "/api/v1/volunteers",
        json={
            "full_name": "Wolontariusz Zadaniowy",
            "email": email,
            "join_date": "2026-01-01T00:00:00",
        },
    )
    assert response.status_code == 200
    return response.json()


def _create_event(db_session, admin_user) -> CalendarEvent:
    event = CalendarEvent(
        title="Festyn Seniora",
        starts_at=datetime(2026, 8, 1, 10, 0, tzinfo=UTC),
        ends_at=datetime(2026, 8, 1, 14, 0, tzinfo=UTC),
        author_id=admin_user.id,
    )
    db_session.add(event)
    db_session.commit()
    return event


def test_task_full_flow_with_checklist_autocomplete(
    api_client, db_session, admin_user
) -> None:
    department = _create_department(api_client)
    volunteer = _create_volunteer(api_client, "zadaniowy@example.com")
    event = _create_event(db_session, admin_user)

    created = api_client.post(
        "/api/v1/tasks",
        json={
            "title": "Przygotować scenę",
            "description": "Scena na festyn",
            "department_id": department["id"],
            "event_id": event.id,
            "due_date": "2026-07-30",
            "assignee_ids": [volunteer["id"]],
            "checklist": ["Zamówić podest", "Rozstawić nagłośnienie"],
        },
    )
    assert created.status_code == 200
    task = created.json()
    assert task["status"] == "DO_ZROBIENIA"
    assert task["department_name"] == "Remonty"
    assert task["event_title"] == "Festyn Seniora"
    assert task["checklist_total"] == 2
    assert task["checklist_done"] == 0
    assert task["assignees"][0]["volunteer_id"] == volunteer["id"]

    first, second = task["checklist"]
    ticked = api_client.patch(
        f"/api/v1/tasks/{task['id']}/checklist/{first['id']}",
        json={"is_done": True},
    ).json()
    assert ticked["checklist_done"] == 1
    assert ticked["status"] == "DO_ZROBIENIA"

    done = api_client.patch(
        f"/api/v1/tasks/{task['id']}/checklist/{second['id']}",
        json={"is_done": True},
    ).json()
    assert done["status"] == "ZROBIONE"
    assert done["completed_at"] is not None

    reopened = api_client.patch(
        f"/api/v1/tasks/{task['id']}/checklist/{first['id']}",
        json={"is_done": False},
    ).json()
    assert reopened["status"] == "W_TRAKCIE"
    assert reopened["completed_at"] is None


def test_task_filters_and_manual_status(api_client, db_session, admin_user) -> None:
    department = _create_department(api_client, name="Media")
    other = _create_department(api_client, name="Szkolenia")
    volunteer = _create_volunteer(api_client, "filtry@example.com")
    event = _create_event(db_session, admin_user)

    task_a = api_client.post(
        "/api/v1/tasks",
        json={
            "title": "Plakaty",
            "department_id": department["id"],
            "event_id": event.id,
            "assignee_ids": [volunteer["id"]],
        },
    ).json()
    api_client.post(
        "/api/v1/tasks",
        json={"title": "Prezentacja", "department_id": other["id"]},
    )

    by_department = api_client.get(
        "/api/v1/tasks", params={"department_id": department["id"]}
    ).json()
    assert [item["id"] for item in by_department] == [task_a["id"]]

    by_event = api_client.get("/api/v1/tasks", params={"event_id": event.id}).json()
    assert [item["id"] for item in by_event] == [task_a["id"]]

    by_volunteer = api_client.get(
        "/api/v1/tasks", params={"volunteer_id": volunteer["id"]}
    ).json()
    assert [item["id"] for item in by_volunteer] == [task_a["id"]]

    manual = api_client.patch(
        f"/api/v1/tasks/{task_a['id']}", json={"status": "ZROBIONE"}
    ).json()
    assert manual["completed_at"] is not None

    by_status = api_client.get(
        "/api/v1/tasks", params={"status": "ZROBIONE"}
    ).json()
    assert [item["id"] for item in by_status] == [task_a["id"]]

    reopened = api_client.patch(
        f"/api/v1/tasks/{task_a['id']}", json={"status": "W_TRAKCIE"}
    ).json()
    assert reopened["completed_at"] is None


def test_task_validations(api_client) -> None:
    department = _create_department(api_client, name="Gastronomia")

    missing_department = api_client.post(
        "/api/v1/tasks", json={"title": "X", "department_id": 12345}
    )
    assert missing_department.status_code == 404

    missing_event = api_client.post(
        "/api/v1/tasks",
        json={"title": "X", "department_id": department["id"], "event_id": 999},
    )
    assert missing_event.status_code == 404

    missing_volunteer = api_client.post(
        "/api/v1/tasks",
        json={
            "title": "X",
            "department_id": department["id"],
            "assignee_ids": [777],
        },
    )
    assert missing_volunteer.status_code == 404

    task = api_client.post(
        "/api/v1/tasks", json={"title": "OK", "department_id": department["id"]}
    ).json()
    bad_status = api_client.patch(
        f"/api/v1/tasks/{task['id']}", json={"status": "NIEZNANY"}
    )
    assert bad_status.status_code == 422


def test_task_delete_and_checklist_management(api_client) -> None:
    department = _create_department(api_client, name="Muzyczni")
    task = api_client.post(
        "/api/v1/tasks", json={"title": "Próba", "department_id": department["id"]}
    ).json()

    with_item = api_client.post(
        f"/api/v1/tasks/{task['id']}/checklist", json={"label": "Zarezerwować salę"}
    ).json()
    assert with_item["checklist_total"] == 1
    item_id = with_item["checklist"][0]["id"]

    renamed = api_client.patch(
        f"/api/v1/tasks/{task['id']}/checklist/{item_id}",
        json={"label": "Zarezerwować salę prób"},
    ).json()
    assert renamed["checklist"][0]["label"] == "Zarezerwować salę prób"

    without_item = api_client.delete(
        f"/api/v1/tasks/{task['id']}/checklist/{item_id}"
    ).json()
    assert without_item["checklist_total"] == 0

    deleted = api_client.delete(f"/api/v1/tasks/{task['id']}")
    assert deleted.status_code == 200
    assert api_client.get(f"/api/v1/tasks/{task['id']}").status_code == 404


def test_manual_status_wins_over_checklist_automation(api_client) -> None:
    """Review fix: a manual status decision is never overridden by the automation."""
    department = _create_department(api_client, name="Pomoc indywidualna")
    task = api_client.post(
        "/api/v1/tasks",
        json={
            "title": "Zadanie reczne",
            "department_id": department["id"],
            "checklist": ["Punkt 1", "Punkt 2"],
        },
    ).json()

    manual = api_client.patch(
        f"/api/v1/tasks/{task['id']}", json={"status": "ZROBIONE"}
    ).json()
    assert manual["status"] == "ZROBIONE"
    assert manual["completed_at"] is not None

    first = task["checklist"][0]
    after_tick = api_client.patch(
        f"/api/v1/tasks/{task['id']}/checklist/{first['id']}",
        json={"is_done": True},
    ).json()
    assert after_tick["status"] == "ZROBIONE"
    assert after_tick["completed_at"] is not None

    after_untick = api_client.patch(
        f"/api/v1/tasks/{task['id']}/checklist/{first['id']}",
        json={"is_done": False},
    ).json()
    assert after_untick["status"] == "ZROBIONE"


def test_adding_item_reopens_auto_completed_task(api_client) -> None:
    """Review fix: reconcile runs after the new item is flushed."""
    department = _create_department(api_client, name="Zbieranie funduszy")
    task = api_client.post(
        "/api/v1/tasks",
        json={
            "title": "Kwesta",
            "department_id": department["id"],
            "checklist": ["Puszki"],
        },
    ).json()

    item = task["checklist"][0]
    done = api_client.patch(
        f"/api/v1/tasks/{task['id']}/checklist/{item['id']}",
        json={"is_done": True},
    ).json()
    assert done["status"] == "ZROBIONE"

    reopened = api_client.post(
        f"/api/v1/tasks/{task['id']}/checklist", json={"label": "Identyfikatory"}
    ).json()
    assert reopened["status"] == "W_TRAKCIE"
    assert reopened["completed_at"] is None


def test_blank_title_and_label_rejected(api_client) -> None:
    """Review fix: whitespace-only text is rejected after strip."""
    department = _create_department(api_client, name="Klub seniora")
    blank_title = api_client.post(
        "/api/v1/tasks", json={"title": "   ", "department_id": department["id"]}
    )
    assert blank_title.status_code == 422

    task = api_client.post(
        "/api/v1/tasks", json={"title": "OK", "department_id": department["id"]}
    ).json()
    blank_label = api_client.post(
        f"/api/v1/tasks/{task['id']}/checklist", json={"label": "   "}
    )
    assert blank_label.status_code == 422
