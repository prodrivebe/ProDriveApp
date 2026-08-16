"""Notification endpoint tests."""

from fastapi.testclient import TestClient


def test_driver_receives_notification_on_assignment(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Assigned driver receives an in-app notification."""
    admin_headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
    customer_response = client.post(
        "/api/v1/customers",
        headers=admin_headers,
        json={"company_name": "Notify Customer GmbH"},
    )
    customer_id = customer_response.json()["data"]["id"]
    user_response = client.post(
        "/api/v1/users",
        headers=admin_headers,
        json={
            "first_name": "Notify",
            "last_name": "Driver",
            "email": "notify.driver@example.com",
            "password": "Driver123!",
            "role": "DRIVER",
            "is_active": True,
        },
    )
    user_id = user_response.json()["data"]["id"]
    driver_response = client.post(
        "/api/v1/drivers",
        headers=admin_headers,
        json={"user_id": user_id, "active": True},
    )
    driver_id = driver_response.json()["data"]["id"]
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

    driver_login = client.post(
        "/api/v1/auth/login",
        json={
            "email": "notify.driver@example.com",
            "password": "Driver123!",
        },
    )
    driver_headers = {
        "Authorization": f"Bearer {driver_login.json()['data']['access_token']}"
    }
    notifications_response = client.get("/api/v1/notifications", headers=driver_headers)

    assert notifications_response.status_code == 200
    notifications = notifications_response.json()["data"]
    assert len(notifications) >= 1
    assert notifications[0]["type"] == "ORDER_ASSIGNED"
    assert notifications[0]["order_id"] == order_id


def test_user_can_mark_notification_read(client: TestClient, admin_tokens: dict[str, str]) -> None:
    """User can mark a notification as read."""
    headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
    list_response = client.get("/api/v1/notifications", headers=headers)
    assert list_response.status_code == 200

    mark_all_response = client.post("/api/v1/notifications/read-all", headers=headers)
    assert mark_all_response.status_code == 200
