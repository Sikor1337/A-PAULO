"""Integration tests for the departments module (PAP-84)."""


def _create_volunteer(api_client, email: str, name: str = "Wolontariusz Testowy"):
    response = api_client.post(
        "/api/v1/volunteers",
        json={
            "full_name": name,
            "email": email,
            "join_date": "2026-01-01T00:00:00",
        },
    )
    assert response.status_code == 200
    return response.json()


def _create_department(api_client, name: str = "Dział Porządkowy", icon: str = "🧹"):
    response = api_client.post(
        "/api/v1/departments",
        json={"name": name, "icon": icon, "description": "Sprzątanie"},
    )
    assert response.status_code == 200
    return response.json()


def test_department_crud_flow(api_client) -> None:
    department = _create_department(api_client)
    assert department["name"] == "Dział Porządkowy"
    assert department["is_archived"] is False
    assert department["members"] == []

    listing = api_client.get("/api/v1/departments").json()
    assert [item["name"] for item in listing] == ["Dział Porządkowy"]
    assert listing[0]["member_count"] == 0

    updated = api_client.patch(
        f"/api/v1/departments/{department['id']}",
        json={"description": "Nowy opis"},
    )
    assert updated.status_code == 200
    assert updated.json()["description"] == "Nowy opis"


def test_department_name_must_be_unique(api_client) -> None:
    _create_department(api_client, name="Media")
    duplicate = api_client.post(
        "/api/v1/departments", json={"name": "media", "icon": "📱"}
    )
    assert duplicate.status_code == 409


def test_department_archive_instead_of_delete(api_client) -> None:
    department = _create_department(api_client, name="Remonty", icon="🔨")

    archived = api_client.patch(
        f"/api/v1/departments/{department['id']}", json={"is_archived": True}
    )
    assert archived.status_code == 200
    assert archived.json()["is_archived"] is True

    default_listing = api_client.get("/api/v1/departments").json()
    assert default_listing == []
    full_listing = api_client.get(
        "/api/v1/departments", params={"include_archived": True}
    ).json()
    assert [item["name"] for item in full_listing] == ["Remonty"]

    # There is deliberately no DELETE /departments/{id} endpoint.
    response = api_client.delete(f"/api/v1/departments/{department['id']}")
    assert response.status_code == 405


def test_membership_add_remove_and_duplicates(api_client) -> None:
    department = _create_department(api_client)
    volunteer = _create_volunteer(api_client, "czlonek@example.com")

    added = api_client.post(
        f"/api/v1/departments/{department['id']}/members",
        json={"volunteer_id": volunteer["id"]},
    )
    assert added.status_code == 200
    members = added.json()["members"]
    assert len(members) == 1
    assert members[0]["volunteer_id"] == volunteer["id"]
    assert members[0]["full_name"] == "Wolontariusz Testowy"

    duplicate = api_client.post(
        f"/api/v1/departments/{department['id']}/members",
        json={"volunteer_id": volunteer["id"]},
    )
    assert duplicate.status_code == 409

    listing = api_client.get("/api/v1/departments").json()
    assert listing[0]["member_count"] == 1

    removed = api_client.delete(
        f"/api/v1/departments/{department['id']}/members/{volunteer['id']}"
    )
    assert removed.status_code == 200
    assert removed.json()["members"] == []


def test_membership_rejects_unknown_volunteer_and_archived_department(
    api_client,
) -> None:
    department = _create_department(api_client)

    missing = api_client.post(
        f"/api/v1/departments/{department['id']}/members",
        json={"volunteer_id": 12345},
    )
    assert missing.status_code == 404

    api_client.patch(
        f"/api/v1/departments/{department['id']}", json={"is_archived": True}
    )
    volunteer = _create_volunteer(api_client, "nowy@example.com")
    blocked = api_client.post(
        f"/api/v1/departments/{department['id']}/members",
        json={"volunteer_id": volunteer["id"]},
    )
    assert blocked.status_code == 422


def test_self_service_join_approve_and_leave(api_client) -> None:
    """PAP-91: a volunteer requests to join, is approved, then leaves."""
    department = _create_department(api_client, name="Wolontariat")
    # The current user (admin) needs a matching volunteer profile to join.
    _create_volunteer(api_client, "admin@example.com", name="Admin Wolontariusz")

    joined = api_client.post(f"/api/v1/departments/{department['id']}/join")
    assert joined.status_code == 200
    members = joined.json()["members"]
    assert len(members) == 1
    assert members[0]["membership_status"] == "PENDING"
    volunteer_id = members[0]["volunteer_id"]

    # Pending requests are not counted as full members.
    assert api_client.get("/api/v1/departments").json()[0]["member_count"] == 0

    # A second request while one is pending is a conflict.
    assert (
        api_client.post(f"/api/v1/departments/{department['id']}/join").status_code
        == 409
    )

    approved = api_client.post(
        f"/api/v1/departments/{department['id']}/members/{volunteer_id}/approve"
    )
    assert approved.status_code == 200
    assert approved.json()["members"][0]["membership_status"] == "ACTIVE"
    assert api_client.get("/api/v1/departments").json()[0]["member_count"] == 1

    # Approving an already active member is a conflict.
    assert (
        api_client.post(
            f"/api/v1/departments/{department['id']}/members/{volunteer_id}/approve"
        ).status_code
        == 409
    )

    left = api_client.delete(f"/api/v1/departments/{department['id']}/members/me")
    assert left.status_code == 200
    assert left.json()["members"] == []


def test_join_needs_a_volunteer_profile_and_leave_needs_membership(
    api_client,
) -> None:
    department = _create_department(api_client, name="Bez profilu")
    # No volunteer carries the current user's e-mail yet.
    assert (
        api_client.post(f"/api/v1/departments/{department['id']}/join").status_code
        == 404
    )
    _create_volunteer(api_client, "admin@example.com")
    # Leaving a department you never joined is a clean 404.
    assert (
        api_client.delete(
            f"/api/v1/departments/{department['id']}/members/me"
        ).status_code
        == 404
    )


def test_cannot_join_an_archived_department(api_client) -> None:
    department = _create_department(api_client, name="Zamkniety")
    _create_volunteer(api_client, "admin@example.com")
    api_client.patch(
        f"/api/v1/departments/{department['id']}", json={"is_archived": True}
    )
    assert (
        api_client.post(f"/api/v1/departments/{department['id']}/join").status_code
        == 422
    )


def test_manager_added_member_is_active_immediately(api_client) -> None:
    department = _create_department(api_client, name="Zarzadzany")
    volunteer = _create_volunteer(api_client, "aktywny@example.com")
    added = api_client.post(
        f"/api/v1/departments/{department['id']}/members",
        json={"volunteer_id": volunteer["id"]},
    )
    assert added.status_code == 200
    assert added.json()["members"][0]["membership_status"] == "ACTIVE"
