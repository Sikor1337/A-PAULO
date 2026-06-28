def _answers(**extra):
    return {
        "full_name": "Anna Kandydatka",
        "email": "anna.kandydatka@example.com",
        "phone": "+48 123 456 789",
        "social_link": "https://example.com/anna",
        "availability": "Wtorki i czwartki",
        **extra,
    }


def _create_invitation(api_client, email="anna.kandydatka@example.com"):
    response = api_client.post(
        "/api/v1/recruitment/invitations",
        json={"recipient_name": "Anna Kandydatka", "recipient_email": email},
    )
    assert response.status_code == 201
    return response.json()


def test_public_form_submission_and_onboarding_flow(api_client, db_session):
    invitation = _create_invitation(api_client)
    form_response = api_client.get(f"/api/v1/recruitment/form/{invitation['token']}")
    assert form_response.status_code == 200
    assert [field["key"] for field in form_response.json()["fields"]][:3] == [
        "full_name",
        "email",
        "phone",
    ]

    response = api_client.post(
        f"/api/v1/recruitment/submissions/{invitation['token']}",
        json={"answers": _answers()},
    )
    assert response.status_code == 201
    submission = response.json()
    assert submission["status"] == "SUBMITTED"
    assert submission["answers"][0]["label"] == "Imię i nazwisko"

    duplicate = api_client.post(
        f"/api/v1/recruitment/submissions/{invitation['token']}",
        json={"answers": _answers()},
    )
    assert duplicate.status_code == 409

    started = api_client.post(
        f"/api/v1/recruitment/submissions/{submission['id']}/start-onboarding"
    )
    assert started.status_code == 200
    assert started.json()["status"] == "ONBOARDING"

    accepted = api_client.post(
        f"/api/v1/recruitment/submissions/{submission['id']}/accept"
    )
    assert accepted.status_code == 200
    assert accepted.json()["status"] == "ACCEPTED"
    assert accepted.json()["volunteer_id"] is not None


def test_return_allows_resubmission_and_custom_question_is_snapshotted(api_client):
    invitation = _create_invitation(api_client)
    field_response = api_client.post(
        "/api/v1/recruitment/fields",
        json={
            "label": "Dlaczego chcesz dołączyć?",
            "field_type": "textarea",
            "required": True,
        },
    )
    assert field_response.status_code == 201
    field = field_response.json()

    first = api_client.post(
        f"/api/v1/recruitment/submissions/{invitation['token']}",
        json={"answers": _answers(**{field["key"]: "Chcę pomagać."})},
    ).json()
    returned = api_client.post(
        f"/api/v1/recruitment/submissions/{first['id']}/return",
        json={"reason": "Uzupełnij odpowiedź"},
    )
    assert returned.status_code == 200
    assert returned.json()["status"] == "RETURNED"
    reopened = api_client.get(f"/api/v1/recruitment/form/{invitation['token']}")
    assert reopened.status_code == 200
    assert reopened.json()["return_reason"] == "Uzupełnij odpowiedź"

    second = api_client.post(
        f"/api/v1/recruitment/submissions/{invitation['token']}",
        json={"answers": _answers(**{field["key"]: "Chcę pomagać regularnie."})},
    )
    assert second.status_code == 201
    assert second.json()["id"] == first["id"]
    assert second.json()["status"] == "SUBMITTED"
    custom_answer = next(
        answer for answer in second.json()["answers"] if answer["key"] == field["key"]
    )
    assert custom_answer["value"] == "Chcę pomagać regularnie."

    deleted = api_client.delete(f"/api/v1/recruitment/fields/{field['id']}")
    assert deleted.status_code == 204
    details = api_client.get(f"/api/v1/recruitment/submissions/{first['id']}").json()
    assert any(
        answer["label"] == "Dlaczego chcesz dołączyć?" for answer in details["answers"]
    )


def test_invitation_locks_email_and_public_values_are_bounded(api_client):
    invitation = _create_invitation(api_client)

    wrong_email = api_client.post(
        f"/api/v1/recruitment/submissions/{invitation['token']}",
        json={"answers": _answers(email="other@example.com")},
    )
    assert wrong_email.status_code == 422

    too_long = api_client.post(
        f"/api/v1/recruitment/submissions/{invitation['token']}",
        json={"answers": _answers(full_name="A" * 201)},
    )
    assert too_long.status_code == 422

    invalid_type = api_client.post(
        f"/api/v1/recruitment/submissions/{invitation['token']}",
        json={"answers": _answers(phone={"unexpected": True})},
    )
    assert invalid_type.status_code == 422


def test_fields_are_reordered_in_one_request(api_client):
    fields = api_client.get("/api/v1/recruitment/fields").json()
    reversed_ids = [field["id"] for field in reversed(fields)]

    response = api_client.put(
        "/api/v1/recruitment/fields/order", json={"field_ids": reversed_ids}
    )

    assert response.status_code == 200
    assert [field["id"] for field in response.json()] == reversed_ids
