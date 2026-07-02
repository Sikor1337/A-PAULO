from datetime import datetime

from sqlalchemy import select

from app.modules.pi.models.volunteer import Volunteer
from app.modules.security.models import UserGroup
from app.modules.security.models.constants import CAN_MANAGE_RECRUITMENT


def _volunteer(db_session, suffix: str = "departure") -> Volunteer:
    volunteer = Volunteer(
        full_name="Jan Odchodzący",
        email=f"{suffix}@example.com",
        phone="+48 500 100 100",
        status="Aktywny",
        join_date=datetime(2024, 1, 10),
        notes="",
        history="Początek współpracy.",
    )
    db_session.add(volunteer)
    db_session.commit()
    db_session.refresh(volunteer)
    return volunteer


def _answers(**extra):
    return {
        "departure_date": "2026-06-30",
        "departure_reason": "Zmiana sytuacji zawodowej",
        "stay_in_contact": True,
        "future_contact": "Jednorazowe wydarzenia",
        "additional_comments": "Dziękuję za współpracę",
        **extra,
    }


def test_departure_interview_marks_volunteer_as_former(api_client, db_session):
    volunteer = _volunteer(db_session)

    fields = api_client.get("/api/v1/recruitment/departures/fields")
    assert fields.status_code == 200
    assert [field["key"] for field in fields.json()][:3] == [
        "departure_date",
        "departure_reason",
        "stay_in_contact",
    ]

    response = api_client.post(
        "/api/v1/recruitment/departures",
        json={"volunteer_id": volunteer.id, "answers": _answers()},
    )

    assert response.status_code == 201
    assert response.json()["volunteer"]["full_name"] == volunteer.full_name
    assert response.json()["stay_in_contact"] is True
    db_session.refresh(volunteer)
    assert volunteer.status == "Były"
    assert "Odejście 2026-06-30" in volunteer.history

    listed = api_client.get("/api/v1/recruitment/departures")
    assert listed.status_code == 200
    assert listed.json()[0]["volunteer_id"] == volunteer.id

    duplicate = api_client.post(
        "/api/v1/recruitment/departures",
        json={"volunteer_id": volunteer.id, "answers": _answers()},
    )
    assert duplicate.status_code == 409


def test_departure_interview_validates_required_answers(api_client, db_session):
    volunteer = _volunteer(db_session, "missing-answer")

    response = api_client.post(
        "/api/v1/recruitment/departures",
        json={
            "volunteer_id": volunteer.id,
            "answers": _answers(departure_reason=""),
        },
    )

    assert response.status_code == 422
    db_session.refresh(volunteer)
    assert volunteer.status == "Aktywny"


def test_departure_fields_are_saved_atomically(api_client):
    fields = api_client.get("/api/v1/recruitment/departures/fields").json()
    draft = [
        {
            "id": field["id"],
            "label": field["label"],
            "field_type": field["field_type"],
            "required": field["required"],
            "placeholder": field["placeholder"],
            "options": field["options"],
            "is_active": field["is_active"],
        }
        for field in fields
    ]
    draft.append(
        {
            "label": "Co warto poprawić?",
            "field_type": "textarea",
            "required": False,
            "placeholder": "Twoja sugestia",
            "options": [],
            "is_active": True,
        }
    )

    response = api_client.put(
        "/api/v1/recruitment/departures/fields", json={"fields": draft}
    )

    assert response.status_code == 200
    assert response.json()[-1]["label"] == "Co warto poprawić?"


def test_departure_fields_reject_whitespace_question(api_client):
    fields = api_client.get("/api/v1/recruitment/departures/fields").json()
    draft = [
        {
            "id": field["id"],
            "label": "   " if index == 0 else field["label"],
            "field_type": field["field_type"],
            "required": field["required"],
            "placeholder": field["placeholder"],
            "options": field["options"],
            "is_active": field["is_active"],
        }
        for index, field in enumerate(fields)
    ]

    response = api_client.put(
        "/api/v1/recruitment/departures/fields", json={"fields": draft}
    )

    assert response.status_code == 422


def test_recruitment_viewer_cannot_change_departure_data(
    api_client, db_session, admin_user
):
    admin_group = db_session.scalar(
        select(UserGroup).where(UserGroup.system_key == "admin")
    )
    assert admin_group is not None
    admin_group.permissions = [
        permission
        for permission in admin_group.permissions
        if permission.code != CAN_MANAGE_RECRUITMENT
    ]
    db_session.commit()

    fields_response = api_client.get("/api/v1/recruitment/departures/fields")
    assert fields_response.status_code == 200

    update_response = api_client.put(
        "/api/v1/recruitment/departures/fields",
        json={"fields": []},
    )
    assert update_response.status_code == 403

    volunteer = _volunteer(db_session, "view-only")
    create_response = api_client.post(
        "/api/v1/recruitment/departures",
        json={"volunteer_id": volunteer.id, "answers": _answers()},
    )
    assert create_response.status_code == 403
