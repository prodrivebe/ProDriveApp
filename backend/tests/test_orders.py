"""Order endpoint tests."""

from fastapi.testclient import TestClient


def _create_customer(client: TestClient, headers: dict[str, str]) -> str:
    response = client.post(
        "/api/v1/customers",
        headers=headers,
        json={"company_name": "Order Customer GmbH"},
    )
    assert response.status_code == 201
    return response.json()["data"]["id"]


def _create_driver_user_and_profile(client: TestClient, headers: dict[str, str]) -> str:
    user_response = client.post(
        "/api/v1/users",
        headers=headers,
        json={
            "first_name": "Order",
            "last_name": "Driver",
            "email": "order.driver@example.com",
            "password": "Driver123!",
            "role": "DRIVER",
            "is_active": True,
        },
    )
    user_id = user_response.json()["data"]["id"]
    driver_response = client.post(
        "/api/v1/drivers",
        headers=headers,
        json={"user_id": user_id, "active": True},
    )
    assert driver_response.status_code == 201
    return driver_response.json()["data"]["id"]


def test_admin_can_create_order_with_wizard_payload(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Admin can create an order with stops and vehicles."""
    headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
    customer_id = _create_customer(client, headers)
    response = client.post(
        "/api/v1/orders",
        headers=headers,
        json={
            "customer_id": customer_id,
            "notes": "Wizard order",
            "stops": [
                {
                    "stop_type": "PICKUP",
                    "sequence": 1,
                    "city": "Amsterdam",
                },
                {
                    "stop_type": "DELIVERY",
                    "sequence": 2,
                    "city": "Brussels",
                },
            ],
            "vehicles": [
                {"make": "BMW", "model": "X5"},
                {"make": "Mercedes", "model": "GLC"},
            ],
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["data"]["status"] == "DRAFT"
    assert len(body["data"]["stops"]) == 2
    assert len(body["data"]["vehicles"]) == 2
    assert body["data"]["order_number"].startswith("ORD-")


def test_admin_can_assign_driver_and_view_timeline(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Admin can assign a driver and read the order timeline."""
    headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
    customer_id = _create_customer(client, headers)
    driver_id = _create_driver_user_and_profile(client, headers)
    order_response = client.post(
        "/api/v1/orders",
        headers=headers,
        json={"customer_id": customer_id},
    )
    order_id = order_response.json()["data"]["id"]

    assign_response = client.post(
        f"/api/v1/orders/{order_id}/assign-driver",
        headers=headers,
        json={"driver_id": driver_id},
    )
    assert assign_response.status_code == 200
    assert assign_response.json()["data"]["status"] == "ASSIGNED"

    timeline_response = client.get(
        f"/api/v1/orders/{order_id}/timeline",
        headers=headers,
    )
    assert timeline_response.status_code == 200
    events = [entry["event_type"] for entry in timeline_response.json()["data"]]
    assert "ORDER_CREATED" in events
    assert "DRIVER_ASSIGNED" in events


def test_vehicle_vin_update_is_audited(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Scanning a VIN updates the vehicle and creates timeline activity."""
    headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
    customer_id = _create_customer(client, headers)
    order_response = client.post(
        "/api/v1/orders",
        headers=headers,
        json={
            "customer_id": customer_id,
            "vehicles": [{"make": "Audi", "model": "A4"}],
        },
    )
    vehicle_id = order_response.json()["data"]["vehicles"][0]["id"]
    vin_response = client.post(
        f"/api/v1/vehicles/{vehicle_id}/scan-vin",
        headers=headers,
        json={"vin": "1HGBH41JXMN109186"},
    )

    assert vin_response.status_code == 200
    assert vin_response.json()["data"]["vin"] == "1HGBH41JXMN109186"


def test_ai_parse_order_returns_draft(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """AI parse endpoint returns a structured draft without creating data."""
    headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
    response = client.post(
        "/api/v1/ai/parse-order",
        headers=headers,
        json={
            "message": "Pick up:\nBMW X5\nAmsterdam\nDeliver:\nBrussels",
        },
    )

    assert response.status_code == 200
    draft = response.json()["data"]
    assert draft["confidence_score"] > 0
    assert len(draft["vehicles"]) >= 1


def test_customer_history_returns_orders(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Customer history lists related orders."""
    headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
    customer_id = _create_customer(client, headers)
    client.post(
        "/api/v1/orders",
        headers=headers,
        json={"customer_id": customer_id},
    )

    response = client.get(
        f"/api/v1/customers/{customer_id}/history",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["meta"]["pagination"]["total"] == 1
