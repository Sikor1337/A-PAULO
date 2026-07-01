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
