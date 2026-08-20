"""Sprint 11 planning board and loading optimization tests."""

from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from app.common.enums import AISuggestionStatus, AISuggestionType


def _headers(admin_tokens: dict[str, str]) -> dict[str, str]:
    return {"Authorization": f"Bearer {admin_tokens['access_token']}"}


def _create_customer(client: TestClient, headers: dict[str, str]) -> str:
    response = client.post(
        "/api/v1/customers",
        headers=headers,
        json={"company_name": "Planning Customer"},
    )
    assert response.status_code in {200, 201}
    return response.json()["data"]["id"]


def _create_driver(client: TestClient, headers: dict[str, str]) -> str:
    user_response = client.post(
        "/api/v1/users",
        headers=headers,
        json={
            "first_name": "Plan",
            "last_name": "Driver",
            "email": f"plan.driver.{uuid.uuid4().hex[:8]}@example.com",
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
    return driver_response.json()["data"]["id"]


def _create_trailer(client: TestClient, headers: dict[str, str]) -> str:
    response = client.post(
        "/api/v1/trailers",
        headers=headers,
        json={
            "registration_number": f"PL-{uuid.uuid4().hex[:6].upper()}",
            "maximum_vehicle_count": 5,
            "maximum_height": 4.0,
            "maximum_weight": 20000,
            "active": True,
        },
    )
    assert response.status_code == 201
    return response.json()["data"]["id"]


def _create_order(client: TestClient, headers: dict[str, str], customer_id: str) -> str:
    response = client.post(
        "/api/v1/orders",
        headers=headers,
        json={
            "customer_id": customer_id,
            "planned_pickup_date": "2026-08-10",
            "stops": [
                {"stop_type": "PICKUP", "sequence": 1, "city": "Amsterdam"},
                {"stop_type": "DELIVERY", "sequence": 2, "city": "Brussels"},
            ],
            "vehicles": [
                {"make": "BMW", "model": "X5", "estimated_weight": 2200, "estimated_height": 1.75},
                {"make": "Audi", "model": "A4", "estimated_weight": 1500, "estimated_height": 1.45},
            ],
        },
    )
    assert response.status_code == 201
    return response.json()["data"]["id"]


def test_planning_board_returns_columns(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    headers = _headers(admin_tokens)
    customer_id = _create_customer(client, headers)
    _create_order(client, headers, customer_id)
    response = client.get("/api/v1/planning/board", headers=headers)
    assert response.status_code == 200
    data = response.json()["data"]
    assert "columns" in data
    assert "drivers" in data
    assert "unassigned" in data["columns"] or "planned" in data["columns"]


def test_planning_assign_and_optimize_flow(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    headers = _headers(admin_tokens)
    customer_id = _create_customer(client, headers)
    driver_id = _create_driver(client, headers)
    trailer_id = _create_trailer(client, headers)
    order_id = _create_order(client, headers, customer_id)

    assign_response = client.post(
        "/api/v1/planning/assign",
        headers=headers,
        json={
            "order_id": order_id,
            "driver_id": driver_id,
            "trailer_id": trailer_id,
        },
    )
    assert assign_response.status_code == 200
    assert assign_response.json()["data"]["status"] == "ASSIGNED"

    optimize_response = client.post(
        "/api/v1/planning/optimize",
        headers=headers,
        json={"order_id": order_id, "include_route": True},
    )
    assert optimize_response.status_code == 200
    suggestion_id = optimize_response.json()["data"]["suggestion_id"]
    assert optimize_response.json()["data"]["confidence"] > 0

    approve_response = client.post(
        f"/api/v1/ai/suggestions/{suggestion_id}/approve",
        headers=headers,
        json={},
    )
    assert approve_response.status_code == 200
    assert approve_response.json()["data"]["status"] == AISuggestionStatus.APPROVED.value
    assert approve_response.json()["data"]["suggestion_type"] == AISuggestionType.LOADING_OPTIMIZATION.value

    load_plan_response = client.get(f"/api/v1/planning/load-plan/{order_id}", headers=headers)
    assert load_plan_response.status_code == 200
    assert len(load_plan_response.json()["data"]["positions"]) >= 2


def test_planning_validate_detects_duplicate_positions(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    headers = _headers(admin_tokens)
    customer_id = _create_customer(client, headers)
    order_id = _create_order(client, headers, customer_id)
    order = client.get(f"/api/v1/orders/{order_id}", headers=headers).json()["data"]
    vehicles = order["vehicles"]

    response = client.post(
        "/api/v1/planning/validate",
        headers=headers,
        json={
            "order_id": order_id,
            "positions": [
                {
                    "vehicle_id": vehicles[0]["id"],
                    "upper_deck": False,
                    "trailer_position": 1,
                    "loading_order": 1,
                    "unloading_order": 2,
                },
                {
                    "vehicle_id": vehicles[1]["id"],
                    "upper_deck": False,
                    "trailer_position": 1,
                    "loading_order": 2,
                    "unloading_order": 1,
                },
            ],
        },
    )
    assert response.status_code == 200
    assert response.json()["data"]["is_valid"] is False


def test_load_plan_draft_persistence(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    headers = _headers(admin_tokens)
    customer_id = _create_customer(client, headers)
    order_id = _create_order(client, headers, customer_id)
    order = client.get(f"/api/v1/orders/{order_id}", headers=headers).json()["data"]
    vehicle = order["vehicles"][0]

    save_response = client.post(
        "/api/v1/planning/load-plan",
        headers=headers,
        json={
            "order_id": order_id,
            "positions": [
                {
                    "vehicle_id": vehicle["id"],
                    "upper_deck": False,
                    "trailer_position": 1,
                    "loading_order": 1,
                    "unloading_order": 1,
                }
            ],
        },
    )
    assert save_response.status_code == 200
    assert save_response.json()["data"]["status"] == "DRAFT"
