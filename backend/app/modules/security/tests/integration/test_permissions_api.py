def test_admin_can_create_custom_group_from_permission_matrix(
    api_client,
) -> None:
    response = api_client.post(
        "/api/v1/security/groups",
        json={
            "name": "Reviewer",
            "description": "Reviews data",
            "permission_codes": ["CAN_VIEW_USERS", "CAN_VIEW_SECURITY"],
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["name"] == "Reviewer"
    assert {permission["code"] for permission in payload["permissions"]} == {
        "CAN_VIEW_USERS",
        "CAN_VIEW_SECURITY",
    }


def test_unknown_permission_code_is_rejected(api_client) -> None:
    response = api_client.post(
        "/api/v1/security/groups",
        json={
            "name": "Broken",
            "description": "",
            "permission_codes": ["CAN_DO_EVERYTHING"],
        },
    )

    assert response.status_code == 422


def test_group_editor_saves_metadata_permissions_and_users_atomically(
    api_client, admin_user
) -> None:
    created = api_client.post(
        "/api/v1/security/groups",
        json={
            "name": "Editor draft",
            "description": "",
            "permission_codes": [],
        },
    ).json()

    response = api_client.put(
        f"/api/v1/security/groups/{created['id']}",
        json={
            "name": "Reviewer",
            "description": "Reviews data",
            "permission_codes": ["CAN_VIEW_USERS", "CAN_VIEW_SECURITY"],
            "user_ids": [admin_user.id],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["name"] == "Reviewer"
    assert payload["description"] == "Reviews data"
    assert payload["user_ids"] == [admin_user.id]
    assert {permission["code"] for permission in payload["permissions"]} == {
        "CAN_VIEW_USERS",
        "CAN_VIEW_SECURITY",
    }


def test_atomic_group_save_rolls_back_all_changes_on_invalid_permission(
    api_client, admin_user
) -> None:
    created = api_client.post(
        "/api/v1/security/groups",
        json={
            "name": "Original",
            "description": "Before",
            "permission_codes": [],
        },
    ).json()

    response = api_client.put(
        f"/api/v1/security/groups/{created['id']}",
        json={
            "name": "Changed",
            "description": "After",
            "permission_codes": ["CAN_DO_EVERYTHING"],
            "user_ids": [admin_user.id],
        },
    )

    assert response.status_code == 422
    groups = api_client.get("/api/v1/security/groups").json()
    unchanged = next(group for group in groups if group["id"] == created["id"])
    assert unchanged["name"] == "Original"
    assert unchanged["description"] == "Before"
    assert unchanged["permissions"] == []
    assert unchanged["user_ids"] == []
