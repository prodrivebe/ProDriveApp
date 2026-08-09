"""End-to-end beta workflow integration tests."""

from __future__ import annotations

from fastapi.testclient import TestClient


def _headers(admin_tokens: dict[str, str]) -> dict[str, str]:
    return {"Authorization": f"Bearer {admin_tokens['access_token']}"}


def test_e2e_dispatcher_order_to_assignment_flow(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Validate core dispatcher workflow from customer to assignment."""
    headers = _headers(admin_tokens)

    customer_response = client.post(
        "/api/v1/customers",
        headers=headers,
        json={"company_name": "E2E Transport Customer", "city": "Amsterdam"},
    )
    assert customer_response.status_code in {200, 201}
    customer_id = customer_response.json()["data"]["id"]

    user_response = client.post(
        "/api/v1/users",
        headers=headers,
        json={
            "first_name": "E2E",
            "last_name": "Driver",
            "email": "e2e.driver@example.com",
            "password": "Driver123!",
            "role": "DRIVER",
            "is_active": True,
        },
    )
    driver_response = client.post(
        "/api/v1/drivers",
        headers=headers,
        json={"user_id": user_response.json()["data"]["id"], "active": True},
    )
    driver_id = driver_response.json()["data"]["id"]

    trailer_response = client.post(
        "/api/v1/trailers",
        headers=headers,
        json={"registration_number": "E2E-TR-01", "maximum_vehicle_count": 5, "active": True},
    )
    trailer_id = trailer_response.json()["data"]["id"]

    order_response = client.post(
        "/api/v1/orders",
        headers=headers,
        json={
            "customer_id": customer_id,
            "planned_pickup_date": "2026-08-15",
            "stops": [
                {"stop_type": "PICKUP", "sequence": 1, "city": "Amsterdam"},
                {"stop_type": "DELIVERY", "sequence": 2, "city": "Brussels"},
            ],
            "vehicles": [{"make": "BMW", "model": "X5", "estimated_weight": 2200, "estimated_height": 1.75}],
        },
    )
    assert order_response.status_code == 200
    order_id = order_response.json()["data"]["id"]

    assign_response = client.post(
        f"/api/v1/orders/{order_id}/assign-driver",
        headers=headers,
        json={"driver_id": driver_id, "trailer_id": trailer_id},
    )
    assert assign_response.status_code == 200
    assert assign_response.json()["data"]["status"] == "ASSIGNED"

    board_response = client.get("/api/v1/planning/board", headers=headers)
    assert board_response.status_code == 200
    assigned_orders = board_response.json()["data"]["columns"].get("assigned", [])
    assert any(item["id"] == order_id for item in assigned_orders)

    parse_response = client.post(
        "/api/v1/ai/parse-order",
        headers=headers,
        json={"message": "Pick up:\nVW Golf\nBerlin\nDeliver:\nMunich"},
    )
    assert parse_response.status_code == 200
    assert parse_response.json()["data"]["status"] == "PENDING"

    timeline_response = client.get(f"/api/v1/orders/{order_id}/timeline", headers=headers)
    assert timeline_response.status_code == 200
    assert len(timeline_response.json()["data"]) >= 1


def test_readiness_endpoint_reports_dependency_status(client: TestClient) -> None:
    """Readiness endpoint returns structured dependency checks."""
    response = client.get("/api/v1/health/ready")
    assert response.status_code in {200, 503}
    payload = response.json()
    assert "checks" in payload
    assert payload["checks"]["database"] == "ok"
