from fastapi.testclient import TestClient

from app.modules.core_data.models import User
from app.modules.pi.models.volunteer import Volunteer
from app.modules.recruitment.access import get_recruitment_access_token
from app.modules.recruitment.constants import ONBOARDING_MEETING_TYPES
from app.modules.recruitment.models import RecruitmentField, RecruitmentSubmission
from app.modules.security.dependencies import get_current_user


def _candidate(db_session, suffix: str = "anna") -> User:
    user = User(
        username=f"{suffix}.candidate",
        email=f"{suffix}.candidate@example.com",
        first_name="Anna",
        last_name="Kandydatka",
        hashed_password="not-used",
        status="new_volunteer",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def _as_user(api_client, user: User) -> None:
    api_client.app.dependency_overrides[get_current_user] = lambda: user
    if user.status == "new_volunteer":
        api_client.headers["X-Recruitment-Token"] = get_recruitment_access_token()
    else:
        api_client.headers.pop("X-Recruitment-Token", None)


def _answers(user: User, **extra):
    return {
        "full_name": "Anna Kandydatka",
        "email": user.email,
        "phone": "+48 123 456 789",
        "social_link": "https://example.com/anna",
        "availability": "Wtorki i czwartki",
        **extra,
    }


def test_account_form_submission_and_onboarding_flow(
    api_client, db_session, admin_user
):
    candidate = _candidate(db_session)
    _as_user(api_client, candidate)

    form_response = api_client.get("/api/v1/recruitment/form")
    assert form_response.status_code == 200
    assert form_response.json()["applicant_email"] == candidate.email
    assert [field["key"] for field in form_response.json()["fields"]][:3] == [
        "full_name",
        "email",
        "phone",
    ]
    assert api_client.get("/api/v1/recruitment/fields").status_code == 403

    response = api_client.post(
        "/api/v1/recruitment/submissions",
        json={"answers": _answers(candidate, phone="1" * 25)},
    )
    assert response.status_code == 201
    submission = response.json()
    assert submission["status"] == "SUBMITTED"
    assert submission["user_id"] == candidate.id

    duplicate = api_client.post(
        "/api/v1/recruitment/submissions",
        json={"answers": _answers(candidate)},
    )
    assert duplicate.status_code == 409

    _as_user(api_client, admin_user)
    started = api_client.post(
        f"/api/v1/recruitment/submissions/{submission['id']}/start-onboarding"
    )
    assert started.status_code == 200
    assert started.json()["status"] == "ONBOARDING"
    assert {
        meeting["meeting_type"] for meeting in started.json()["onboarding_meetings"]
    } == set(ONBOARDING_MEETING_TYPES)

    premature = api_client.post(
        f"/api/v1/recruitment/submissions/{submission['id']}/accept",
        json={"comment": None},
    )
    assert premature.status_code == 409

    for meeting_type in ONBOARDING_MEETING_TYPES:
        attendance = api_client.put(
            f"/api/v1/recruitment/submissions/{submission['id']}"
            f"/onboarding-meetings/{meeting_type}",
            json={"attended": True},
        )
        assert attendance.status_code == 200
        saved = next(
            meeting
            for meeting in attendance.json()["onboarding_meetings"]
            if meeting["meeting_type"] == meeting_type
        )
        assert saved["attended_at"] is not None

    accepted = api_client.post(
        f"/api/v1/recruitment/submissions/{submission['id']}/accept",
        json={"comment": "Świetnie poradziła sobie podczas wdrożenia."},
    )
    assert accepted.status_code == 200
    assert accepted.json()["status"] == "ACCEPTED"
    assert accepted.json()["decision_comment"].startswith("Świetnie")
    volunteer_id = accepted.json()["volunteer_id"]
    assert volunteer_id is not None
    volunteer = db_session.get(Volunteer, volunteer_id)
    assert volunteer.history == ""
    assert volunteer.notes == ""
    assert Volunteer.__table__.c.phone.type.length == 30
    assert candidate.status == "regular"

    restored = api_client.post(
        f"/api/v1/recruitment/submissions/{submission['id']}/restore-onboarding"
    )
    assert restored.status_code == 200
    assert restored.json()["volunteer_id"] is None
    assert db_session.get(Volunteer, volunteer_id) is None

    accepted_again = api_client.post(
        f"/api/v1/recruitment/submissions/{submission['id']}/accept",
        json={"comment": "Decyzja potwierdzona."},
    )
    assert accepted_again.status_code == 200
    recreated_id = accepted_again.json()["volunteer_id"]
    assert recreated_id is not None
    assert db_session.get(Volunteer, recreated_id).status == "Aktywny"


def test_onboarding_attendance_can_be_corrected(api_client, db_session, admin_user):
    candidate = _candidate(db_session, "attendance")
    _as_user(api_client, candidate)
    submission = api_client.post(
        "/api/v1/recruitment/submissions",
        json={"answers": _answers(candidate)},
    ).json()
    _as_user(api_client, admin_user)
    api_client.post(
        f"/api/v1/recruitment/submissions/{submission['id']}/start-onboarding"
    )

    checked = api_client.put(
        f"/api/v1/recruitment/submissions/{submission['id']}"
        "/onboarding-meetings/CHARISM",
        json={"attended": True},
    )
    assert checked.status_code == 200
    unchecked = api_client.put(
        f"/api/v1/recruitment/submissions/{submission['id']}"
        "/onboarding-meetings/CHARISM",
        json={"attended": False},
    )
    assert unchecked.status_code == 200
    charism = next(
        meeting
        for meeting in unchecked.json()["onboarding_meetings"]
        if meeting["meeting_type"] == "CHARISM"
    )
    assert charism["attended_at"] is None

    invalid = api_client.put(
        f"/api/v1/recruitment/submissions/{submission['id']}"
        "/onboarding-meetings/UNKNOWN",
        json={"attended": True},
    )
    assert invalid.status_code == 422


def test_form_draft_is_saved_once_and_multiselect_is_snapshotted(
    api_client, db_session, admin_user
):
    _as_user(api_client, admin_user)
    fields = api_client.get("/api/v1/recruitment/fields").json()
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
        for field in reversed(fields)
    ]
    draft.append(
        {
            "label": "W jakich obszarach chcesz pomagać?",
            "field_type": "multiselect",
            "required": True,
            "placeholder": "",
            "options": ["Obszar A", "Obszar B", "Obszar C"],
            "is_active": True,
        }
    )
    saved = api_client.put("/api/v1/recruitment/fields", json={"fields": draft})
    assert saved.status_code == 200
    custom = saved.json()[-1]
    assert custom["field_type"] == "multiselect"

    candidate = _candidate(db_session, "multi")
    _as_user(api_client, candidate)
    first = api_client.post(
        "/api/v1/recruitment/submissions",
        json={
            "answers": _answers(candidate, **{custom["key"]: ["Obszar A", "Obszar C"]})
        },
    )
    assert first.status_code == 201
    custom_answer = next(
        answer for answer in first.json()["answers"] if answer["key"] == custom["key"]
    )
    assert custom_answer["value"] == ["Obszar A", "Obszar C"]

    _as_user(api_client, admin_user)
    returned = api_client.post(
        f"/api/v1/recruitment/submissions/{first.json()['id']}/return",
        json={"reason": "Uzupełnij odpowiedź"},
    )
    assert returned.status_code == 200

    _as_user(api_client, candidate)
    reopened = api_client.get("/api/v1/recruitment/form")
    assert reopened.json()["submission_status"] == "RETURNED"
    assert reopened.json()["return_reason"] == "Uzupełnij odpowiedź"
    assert reopened.json()["initial_answers"][custom["key"]] == [
        "Obszar A",
        "Obszar C",
    ]


def test_form_restores_missing_system_fields_without_deleting_custom_fields(
    api_client, db_session, admin_user
):
    custom = RecruitmentField(
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
    _as_user(api_client, admin_user)

    response = api_client.get("/api/v1/recruitment/fields")

    assert response.status_code == 200
    fields = response.json()
    assert [field["key"] for field in fields[:3]] == [
        "full_name",
        "email",
        "phone",
    ]
    assert fields[3]["key"] == "custom_question"
    assert all(field["is_system"] for field in fields[:3])


def test_schema_rejects_invalid_public_values(api_client, db_session):
    candidate = _candidate(db_session, "invalid")
    _as_user(api_client, candidate)

    wrong_email = api_client.post(
        "/api/v1/recruitment/submissions",
        json={"answers": _answers(candidate, email="other@example.com")},
    )
    assert wrong_email.status_code == 422

    too_long = api_client.post(
        "/api/v1/recruitment/submissions",
        json={"answers": _answers(candidate, full_name="A" * 201)},
    )
    assert too_long.status_code == 422

    invalid_type = api_client.post(
        "/api/v1/recruitment/submissions",
        json={"answers": _answers(candidate, phone={"unexpected": True})},
    )
    assert invalid_type.status_code == 422


def test_form_rejects_a_whitespace_only_question(api_client, admin_user):
    _as_user(api_client, admin_user)
    fields = api_client.get("/api/v1/recruitment/fields").json()
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

    response = api_client.put("/api/v1/recruitment/fields", json={"fields": draft})

    assert response.status_code == 422


def test_decision_can_be_reverted_to_onboarding(api_client, db_session, admin_user):
    candidate = _candidate(db_session, "restore")
    _as_user(api_client, candidate)
    submission = api_client.post(
        "/api/v1/recruitment/submissions",
        json={"answers": _answers(candidate)},
    ).json()

    _as_user(api_client, admin_user)
    api_client.post(
        f"/api/v1/recruitment/submissions/{submission['id']}/start-onboarding"
    )
    rejected = api_client.post(
        f"/api/v1/recruitment/submissions/{submission['id']}/reject",
        json={"comment": "Brak dostępności w tym naborze."},
    )
    assert rejected.json()["decision_comment"] == "Brak dostępności w tym naborze."

    restored = api_client.post(
        f"/api/v1/recruitment/submissions/{submission['id']}/restore-onboarding"
    )
    assert restored.status_code == 200
    assert restored.json()["status"] == "ONBOARDING"
    assert restored.json()["decision_comment"] is None


def test_list_submissions_normalizes_legacy_object_answers(
    api_client, db_session, admin_user
):
    candidate = _candidate(db_session, "legacy")
    submission = RecruitmentSubmission(
        user_id=candidate.id,
        full_name="Anna Legacy",
        email=candidate.email,
        phone="123456789",
        social_link="",
        availability="Wtorki",
        answers={"full_name": "Anna Legacy", "contact_ok": True},
        status="SUBMITTED",
    )
    db_session.add(submission)
    db_session.commit()
    _as_user(api_client, admin_user)

    response = api_client.get(
        "/api/v1/recruitment/submissions", params={"skip": 0, "limit": 1000}
    )

    assert response.status_code == 200
    answers = response.json()[0]["answers"]
    assert answers[0]["key"] == "full_name"
    assert answers[1]["field_type"] == "checkbox"


def test_access_link_is_opaque_and_candidate_endpoints_require_it(
    api_client, db_session, admin_user
):
    _as_user(api_client, admin_user)
    link_response = api_client.get("/api/v1/recruitment/access-link")
    assert link_response.status_code == 200
    path = link_response.json()["path"]
    assert path.startswith("/recrutation/")
    assert len(path.rsplit("/", 1)[-1]) == 64

    candidate = _candidate(db_session, "guarded")
    _as_user(api_client, candidate)
    api_client.headers.pop("X-Recruitment-Token")
    assert api_client.get("/api/v1/recruitment/form").status_code == 404


def test_main_application_registers_production_recruitment_routes():
    from app.main import app

    paths = set(app.openapi()["paths"])
    assert "/api/v1/recruitment/fields" in paths
    assert "/api/v1/recruitment/submissions" in paths
    assert "/api/v1/recruitment/access-link" in paths

    with TestClient(app) as client:
        assert client.get("/api/v1/recruitment/fields").status_code != 404
