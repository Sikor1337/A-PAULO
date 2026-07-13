from datetime import datetime

from sqlalchemy import select

from app.modules.core_data.models import User
from app.modules.pi.models.volunteer import Volunteer
from app.modules.recruitment.models import DepartureField
from app.modules.security.dependencies import get_current_user
from app.modules.security.models import Permission, UserGroup, security_user_groups
from app.modules.security.models.constants import (
    CAN_MANAGE_RECRUITMENT,
    CAN_SUBMIT_DEPARTURE_SURVEY,
)


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


def _grant_departure_submit(db_session, user: User) -> None:
    """Give a user the self-service departure-survey permission (PAP-96)."""
    perm = (
        db_session.query(Permission).filter_by(code=CAN_SUBMIT_DEPARTURE_SURVEY).one()
    )
    group = UserGroup(
        name=f"Odejście-{user.username}",
        description="Może wypełnić własną ankietę odejścia",
        permissions=[perm],
    )
    db_session.add(group)
    db_session.flush()
    db_session.execute(
        security_user_groups.insert(),
        {"user_id": user.id, "group_id": group.id},
    )
    db_session.commit()


def _user(db_session, volunteer: Volunteer, suffix: str = "departure-user") -> User:
    user = User(
        username=suffix,
        email=volunteer.email,
        first_name="Jan",
        last_name="Odchodzący",
        hashed_password="not-used",
        status="regular",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    _grant_departure_submit(db_session, user)
    return user


def _as_user(api_client, user: User) -> None:
    api_client.app.dependency_overrides[get_current_user] = lambda: user


def _answers(**extra):
    return {
        "departure_date": "2026-06-30",
        "departure_reason": "Zmiana sytuacji zawodowej",
        "stay_in_contact": True,
        "future_contact": "Jednorazowe wydarzenia",
        "additional_comments": "Dziękuję za współpracę",
        **extra,
    }


def test_volunteer_submits_own_departure_interview(api_client, db_session, admin_user):
    volunteer = _volunteer(db_session)
    user = _user(db_session, volunteer)
    _as_user(api_client, user)

    survey = api_client.get("/api/v1/recruitment/departures/me")
    assert survey.status_code == 200
    assert survey.json()["volunteer"]["id"] == volunteer.id
    assert survey.json()["interview"] is None
    assert [field["key"] for field in survey.json()["fields"]][:3] == [
        "departure_date",
        "departure_reason",
        "stay_in_contact",
    ]

    response = api_client.post(
        "/api/v1/recruitment/departures/me",
        json={"answers": _answers()},
    )

    assert response.status_code == 201
    assert response.json()["volunteer"]["full_name"] == volunteer.full_name
    assert response.json()["stay_in_contact"] is True
    assert response.json()["completed_by_id"] == user.id
    db_session.refresh(volunteer)
    assert volunteer.status == "Aktywny"
    assert volunteer.history == "Początek współpracy."

    mine = api_client.get("/api/v1/recruitment/departures/me")
    assert mine.status_code == 200
    assert mine.json()["interview"]["id"] == response.json()["id"]

    original_reason = next(
        answer
        for answer in response.json()["answers"]
        if answer["key"] == "departure_reason"
    )
    reason_field = db_session.scalar(
        select(DepartureField).where(DepartureField.key == "departure_reason")
    )
    assert reason_field is not None
    reason_field.label = "Nowa treść pytania"
    db_session.commit()

    updated = api_client.put(
        "/api/v1/recruitment/departures/me",
        json={"answers": _answers(departure_reason="Nowy powód")},
    )
    assert updated.status_code == 200
    updated_reason = next(
        answer
        for answer in updated.json()["answers"]
        if answer["key"] == "departure_reason"
    )
    assert updated_reason["value"] == "Nowy powód"
    assert updated_reason["label"] == original_reason["label"]
    db_session.refresh(volunteer)
    assert volunteer.status == "Aktywny"

    _as_user(api_client, admin_user)
    listed = api_client.get("/api/v1/recruitment/departures")
    assert listed.status_code == 200
    assert listed.json()[0]["volunteer_id"] == volunteer.id

    _as_user(api_client, user)
    duplicate = api_client.post(
        "/api/v1/recruitment/departures/me",
        json={"answers": _answers()},
    )
    assert duplicate.status_code == 409


def test_departure_interview_validates_required_answers(api_client, db_session):
    volunteer = _volunteer(db_session, "missing-answer")
    user = _user(db_session, volunteer, "missing-answer-user")
    _as_user(api_client, user)

    response = api_client.post(
        "/api/v1/recruitment/departures/me",
        json={
            "answers": _answers(departure_reason=""),
        },
    )

    assert response.status_code == 422
    db_session.refresh(volunteer)
    assert volunteer.status == "Aktywny"


def test_user_cannot_submit_departure_for_an_unrelated_volunteer(
    api_client, db_session
):
    volunteer = _volunteer(db_session, "unrelated-volunteer")
    user = User(
        username="unrelated-user",
        email="unrelated-user@example.com",
        first_name="Inny",
        last_name="Użytkownik",
        hashed_password="not-used",
        status="regular",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    _grant_departure_submit(db_session, user)
    _as_user(api_client, user)

    response = api_client.post(
        "/api/v1/recruitment/departures/me",
        json={"answers": _answers()},
    )

    assert response.status_code == 404
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


def test_departure_field_read_does_not_create_missing_reference_data(
    api_client, db_session
):
    departure_date = (
        db_session.query(DepartureField).filter_by(key="departure_date").one()
    )
    db_session.delete(departure_date)
    custom = DepartureField(
        key="custom_question",
        label="Pytanie dodatkowe",
        field_type="text",
        required=False,
        placeholder="",
        options=[],
        position=0,
        is_active=True,
        is_system=False,
    )
    db_session.add(custom)
    db_session.commit()

    response = api_client.get("/api/v1/recruitment/departures/fields")

    assert response.status_code == 200
    fields = response.json()
    assert "departure_date" not in {field["key"] for field in fields}
    assert "custom_question" in {field["key"] for field in fields}


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

    create_response = api_client.post(
        "/api/v1/recruitment/departures",
        json={"answers": _answers()},
    )
    assert create_response.status_code == 405
