"""End-to-end API coverage for PAP-90."""

from app.modules.recruitment.beneficiary_access import get_beneficiary_access_token
from app.modules.recruitment.beneficiary_constants import (
    BENEFICIARY_RECRUITMENT_TOKEN_HEADER,
)


def _headers() -> dict[str, str]:
    return {BENEFICIARY_RECRUITMENT_TOKEN_HEADER: get_beneficiary_access_token()}


def _answers() -> dict:
    return {
        "full_name": "Jan Potrzebujący",
        "address": "ul. Dobra 1, Kraków",
        "phone": "123456789",
        "reporter_name": "Anna Zgłaszająca",
        "reporter_phone": "987654321",
        "help_needed": "Regularne zakupy i rozmowa.",
        "rodo_consent": True,
    }


def _submit(api_client) -> dict:
    form = api_client.get(
        "/api/v1/beneficiary-recruitment/public/form", headers=_headers()
    )
    assert form.status_code == 200
    response = api_client.post(
        "/api/v1/beneficiary-recruitment/public/submissions",
        headers=_headers(),
        json={
            "answers": _answers(),
            "form_token": form.json()["form_token"],
            "website": "",
        },
    )
    assert response.status_code == 201
    return response.json()


def test_public_form_requires_secret_link_and_accepts_submission(api_client) -> None:
    hidden = api_client.get("/api/v1/beneficiary-recruitment/public/form")
    assert hidden.status_code == 404

    submission = _submit(api_client)
    assert submission["status"] == "NEW"
    assert submission["full_name"] == "Jan Potrzebujący"

    listed = api_client.get("/api/v1/beneficiary-recruitment/submissions")
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()] == [submission["id"]]


def test_public_form_rejects_honeypot_and_invalid_proof(api_client) -> None:
    rejected = api_client.post(
        "/api/v1/beneficiary-recruitment/public/submissions",
        headers=_headers(),
        json={
            "answers": _answers(),
            "form_token": "invalid-form-token",
            "website": "bot.example",
        },
    )
    assert rejected.status_code == 422


def test_submission_can_create_beneficiary_then_archive_and_delete(api_client) -> None:
    submission = _submit(api_client)
    created = api_client.post(
        f"/api/v1/beneficiary-recruitment/submissions/{submission['id']}/create-beneficiary",
        json={"group_id": None},
    )
    assert created.status_code == 200
    assert created.json()["status"] == "BENEFICIARY_CREATED"
    beneficiary_id = created.json()["beneficiary_id"]
    beneficiary = api_client.get(f"/api/v1/beneficiaries/{beneficiary_id}")
    assert beneficiary.status_code == 200
    assert beneficiary.json()["full_name"] == submission["full_name"]

    archived = api_client.post(
        f"/api/v1/beneficiary-recruitment/submissions/{submission['id']}/archive"
    )
    assert archived.status_code == 200
    assert archived.json()["status"] == "ARCHIVED"
    assert api_client.get("/api/v1/beneficiary-recruitment/submissions").json() == []

    deleted = api_client.delete(
        f"/api/v1/beneficiary-recruitment/submissions/{submission['id']}"
    )
    assert deleted.status_code == 204
    assert api_client.get(f"/api/v1/beneficiaries/{beneficiary_id}").status_code == 200


def test_new_submission_must_be_decided_before_archive_or_delete(api_client) -> None:
    submission = _submit(api_client)
    path = f"/api/v1/beneficiary-recruitment/submissions/{submission['id']}"
    assert api_client.post(f"{path}/archive").status_code == 409
    assert api_client.delete(path).status_code == 409

    rejected = api_client.post(
        f"{path}/reject", json={"comment": "Poza obszarem działania"}
    )
    assert rejected.status_code == 200
    assert rejected.json()["status"] == "REJECTED"
    assert api_client.delete(path).status_code == 204


def test_staff_submission_list_is_paginated(api_client) -> None:
    first = _submit(api_client)
    second = _submit(api_client)

    first_page = api_client.get(
        "/api/v1/beneficiary-recruitment/submissions",
        params={"skip": 0, "limit": 1},
    )
    second_page = api_client.get(
        "/api/v1/beneficiary-recruitment/submissions",
        params={"skip": 1, "limit": 1},
    )

    assert first_page.status_code == 200
    assert second_page.status_code == 200
    assert first_page.json()[0]["id"] == second["id"]
    assert second_page.json()[0]["id"] == first["id"]
