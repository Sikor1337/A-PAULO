from sqlalchemy.orm import Session

from app.modules.security.models import Permission
from app.modules.security.models.constants import PERMISSION_CATALOG


def _seed_catalog(session: Session) -> None:
    session.add_all(
        [
            Permission(code=code, name=name, category=category)
            for code, name, category in PERMISSION_CATALOG
        ]
    )
    session.commit()


def test_admin_can_create_custom_group_from_permission_matrix(
    api_client,
    db_session: Session,
) -> None:
    _seed_catalog(db_session)

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


def test_unknown_permission_code_is_rejected(api_client, db_session: Session) -> None:
    _seed_catalog(db_session)

    response = api_client.post(
        "/api/v1/security/groups",
        json={
            "name": "Broken",
            "description": "",
            "permission_codes": ["CAN_DO_EVERYTHING"],
        },
    )

    assert response.status_code == 422
