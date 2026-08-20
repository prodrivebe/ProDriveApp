"""Regression tests for driver display name enrichment."""

from fastapi.testclient import TestClient


def _create_driver_user(client: TestClient, headers: dict[str, str]) -> tuple[str, str]:
    user_response = client.post(
        "/api/v1/users",
        headers=headers,
        json={
            "first_name": "Vadym",
            "last_name": "Seniv",
            "email": "vadym.seniv@example.com",
            "password": "Driver123!",
            "role": "DRIVER",
        },
    )
    assert user_response.status_code == 201, user_response.text
    user_id = user_response.json()["data"]["id"]

    driver_response = client.post(
        "/api/v1/drivers",
        headers=headers,
        json={"user_id": user_id, "phone": "+32470123456", "active": True},
    )
    assert driver_response.status_code == 201, driver_response.text
    driver_body = driver_response.json()["data"]
    return driver_body["id"], driver_body["display_name"]


def test_driver_list_returns_display_name(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Drivers list must expose display_name with the linked user's real name."""
    headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
    driver_id, display_name = _create_driver_user(client, headers)
    assert display_name == "Vadym Seniv"

    list_response = client.get(
        "/api/v1/drivers",
        headers=headers,
        params={"page": 1, "page_size": 100},
    )
    assert list_response.status_code == 200, list_response.text
    drivers = list_response.json()["data"]
    listed = next(item for item in drivers if item["id"] == driver_id)
    assert listed["first_name"] == "Vadym"
    assert listed["last_name"] == "Seniv"
    assert listed["display_name"] == "Vadym Seniv"


def test_driver_detail_returns_display_name(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Single driver fetch must include display_name."""
    headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
    driver_id, _ = _create_driver_user(client, headers)
    detail_response = client.get(f"/api/v1/drivers/{driver_id}", headers=headers)
    assert detail_response.status_code == 200, detail_response.text
    payload = detail_response.json()["data"]
    assert payload["display_name"] == "Vadym Seniv"
