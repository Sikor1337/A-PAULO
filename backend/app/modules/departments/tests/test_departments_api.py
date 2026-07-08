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
