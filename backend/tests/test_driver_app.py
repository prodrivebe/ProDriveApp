"""Driver app API tests."""

import io

from fastapi.testclient import TestClient

MINIMAL_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
    b"\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
    b"\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01"
    b"\x0d\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)


def _create_customer(client: TestClient, headers: dict[str, str]) -> str:
    response = client.post(
        "/api/v1/customers",
        headers=headers,
        json={"company_name": "Driver App Customer"},
    )
    assert response.status_code == 201
    return response.json()["data"]["id"]


def _create_driver_with_login(
    client: TestClient,
    admin_headers: dict[str, str],
) -> tuple[str, dict[str, str]]:
    user_response = client.post(
        "/api/v1/users",
        headers=admin_headers,
        json={
            "first_name": "Mobile",
            "last_name": "Driver",
            "email": "mobile.driver@example.com",
            "password": "Driver123!",
            "role": "DRIVER",
            "is_active": True,
        },
    )
    assert user_response.status_code == 201
    user_id = user_response.json()["data"]["id"]
    driver_response = client.post(
        "/api/v1/drivers",
        headers=admin_headers,
        json={"user_id": user_id, "active": True},
    )
    assert driver_response.status_code == 201
    driver_id = driver_response.json()["data"]["id"]

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "mobile.driver@example.com", "password": "Driver123!"},
    )
    assert login_response.status_code == 200
    tokens = login_response.json()["data"]
    driver_headers = {"Authorization": f"Bearer {tokens['access_token']}"}
    return driver_id, driver_headers


def test_driver_can_access_me_endpoints(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Driver can read profile, home, and assigned orders."""
    admin_headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
    driver_id, driver_headers = _create_driver_with_login(client, admin_headers)
    customer_id = _create_customer(client, admin_headers)

    order_response = client.post(
        "/api/v1/orders",
        headers=admin_headers,
        json={"customer_id": customer_id},
    )
    order_id = order_response.json()["data"]["id"]
    client.post(
        f"/api/v1/orders/{order_id}/assign-driver",
        headers=admin_headers,
        json={"driver_id": driver_id},
    )

    profile_response = client.get("/api/v1/drivers/me", headers=driver_headers)
    assert profile_response.status_code == 200
    assert profile_response.json()["data"]["id"] == driver_id

    home_response = client.get("/api/v1/drivers/me/home", headers=driver_headers)
    assert home_response.status_code == 200
    home = home_response.json()["data"]
    assert home["current_order"]["id"] == order_id
    assert "Accept or reject" in home["next_action"]

    orders_response = client.get("/api/v1/drivers/me/orders", headers=driver_headers)
    assert orders_response.status_code == 200
    assert orders_response.json()["meta"]["pagination"]["total"] == 1


def test_driver_can_view_assigned_order_details(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Driver can read order details but not unrelated orders."""
    admin_headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
    driver_id, driver_headers = _create_driver_with_login(client, admin_headers)
    customer_id = _create_customer(client, admin_headers)

    assigned_response = client.post(
        "/api/v1/orders",
        headers=admin_headers,
        json={"customer_id": customer_id},
    )
    assigned_id = assigned_response.json()["data"]["id"]
    client.post(
        f"/api/v1/orders/{assigned_id}/assign-driver",
        headers=admin_headers,
        json={"driver_id": driver_id},
    )

    other_response = client.post(
        "/api/v1/orders",
        headers=admin_headers,
        json={"customer_id": customer_id},
    )
    other_id = other_response.json()["data"]["id"]

    allowed = client.get(f"/api/v1/orders/{assigned_id}", headers=driver_headers)
    assert allowed.status_code == 200

    denied = client.get(f"/api/v1/orders/{other_id}", headers=driver_headers)
    assert denied.status_code == 403


def test_driver_workflow_notifies_dispatchers_on_completion(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Completing delivery notifies admin/dispatcher staff."""
    admin_headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
    driver_id, driver_headers = _create_driver_with_login(client, admin_headers)
    customer_id = _create_customer(client, admin_headers)
    order_response = client.post(
        "/api/v1/orders",
        headers=admin_headers,
        json={"customer_id": customer_id},
    )
    order_id = order_response.json()["data"]["id"]
    client.post(
        f"/api/v1/orders/{order_id}/assign-driver",
        headers=admin_headers,
        json={"driver_id": driver_id},
    )

    for path in (
        "accept",
        "arrive-pickup",
        "start-loading",
        "complete-loading",
        "start-transit",
        "arrive-delivery",
        "finish-delivery",
        "complete-delivery",
    ):
        if path == "complete-loading":
            generate = client.post(
                f"/api/v1/orders/{order_id}/cmr/generate",
                headers=driver_headers,
            )
            assert generate.status_code == 200, generate.text
        if path == "finish-delivery":
            upload = client.post(
                f"/api/v1/orders/{order_id}/documents",
                headers=driver_headers,
                files={"file": ("signed-cmr.png", io.BytesIO(MINIMAL_PNG), "image/png")},
                data={"document_type": "CMR"},
            )
            assert upload.status_code == 201, upload.text
        response = client.post(
            f"/api/v1/orders/{order_id}/{path}",
            headers=driver_headers,
        )
        assert response.status_code == 200

    notifications = client.get("/api/v1/notifications", headers=admin_headers)
    assert notifications.status_code == 200
    types = [item["type"] for item in notifications.json()["data"]]
    assert "ORDER_COMPLETED" in types


def test_register_device_token(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Users can register a push device token."""
    headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
    response = client.post(
        "/api/v1/notifications/register-device",
        headers=headers,
        json={"token": "fcm-test-token-123", "platform": "android"},
    )
    assert response.status_code == 201
    assert response.json()["data"]["platform"] == "android"


def test_ai_suggest_empty_km(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Empty kilometer suggestions return heuristic data."""
    headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
    _create_driver_with_login(client, headers)
    response = client.post("/api/v1/ai/suggest-empty-km", headers=headers)
    assert response.status_code == 200
    body = response.json()["data"]
    assert body["confidence_score"] >= 0
    assert len(body["suggestions"]) >= 1
