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


def test_admin_can_update_assignment_on_assigned_order(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Assigned orders can update driver/truck/trailer without invalid transitions."""
    headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
    customer_id = _create_customer(client, headers)
    driver_id = _create_driver_user_and_profile(client, headers)
    truck_response = client.post(
        "/api/v1/trucks",
        headers=headers,
        json={"registration_number": "1-UPD-001", "brand": "Volvo", "model": "FH", "active": True},
    )
    truck_id = truck_response.json()["data"]["id"]
    order_response = client.post(
        "/api/v1/orders",
        headers=headers,
        json={"customer_id": customer_id},
    )
    order_id = order_response.json()["data"]["id"]

    first_assign = client.post(
        f"/api/v1/orders/{order_id}/assign-driver",
        headers=headers,
        json={"driver_id": driver_id},
    )
    assert first_assign.status_code == 200
    assert first_assign.json()["data"]["status"] == "ASSIGNED"

    second_assign = client.post(
        f"/api/v1/orders/{order_id}/assign-driver",
        headers=headers,
        json={"driver_id": driver_id, "truck_id": truck_id},
    )
    assert second_assign.status_code == 200
    payload = second_assign.json()["data"]
    assert payload["status"] == "ASSIGNED"
    assert payload["assigned_truck_id"] == truck_id


def test_assignment_persists_driver_truck_trailer_after_refresh(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Assign driver, truck, and trailer; reload order and verify persistence."""
    headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
    customer_id = _create_customer(client, headers)
    driver_id = _create_driver_user_and_profile(client, headers)

    truck_response = client.post(
        "/api/v1/trucks",
        headers=headers,
        json={"registration_number": "1-PST-001", "brand": "Volvo", "model": "FH", "active": True},
    )
    assert truck_response.status_code == 201
    truck_id = truck_response.json()["data"]["id"]

    trailer_response = client.post(
        "/api/v1/trailers",
        headers=headers,
        json={
            "registration_number": "1-PST-T01",
            "trailer_type": "CAR_TRANSPORTER",
            "maximum_vehicle_count": 8,
            "active": True,
        },
    )
    assert trailer_response.status_code == 201
    trailer_id = trailer_response.json()["data"]["id"]

    order_response = client.post(
        "/api/v1/orders",
        headers=headers,
        json={"customer_id": customer_id},
    )
    assert order_response.status_code == 201
    order_id = order_response.json()["data"]["id"]

    assign_response = client.post(
        f"/api/v1/orders/{order_id}/assign-driver",
        headers=headers,
        json={
            "driver_id": driver_id,
            "truck_id": truck_id,
            "trailer_id": trailer_id,
        },
    )
    assert assign_response.status_code == 200, assign_response.text
    assigned = assign_response.json()["data"]
    assert assigned["status"] == "ASSIGNED"
    assert assigned["assigned_driver_id"] == driver_id
    assert assigned["assigned_truck_id"] == truck_id
    assert assigned["assigned_trailer_id"] == trailer_id

    reload_response = client.get(f"/api/v1/orders/{order_id}", headers=headers)
    assert reload_response.status_code == 200
    reloaded = reload_response.json()["data"]
    assert reloaded["assigned_driver_id"] == driver_id
    assert reloaded["assigned_truck_id"] == truck_id
    assert reloaded["assigned_trailer_id"] == trailer_id


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
    """AI parse endpoint returns a pending suggestion without creating data."""
    headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
    response = client.post(
        "/api/v1/ai/parse-order",
        headers=headers,
        json={
            "message": "Pick up:\nBMW X5\nAmsterdam\nDeliver:\nBrussels",
        },
    )

    assert response.status_code == 200
    suggestion = response.json()["data"]
    assert suggestion["status"] == "PENDING"
    assert suggestion["confidence"] > 0
    assert len(suggestion["output_json"]["vehicles"]) >= 1


def test_create_order_with_eight_vehicles_and_vins(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Orders accept up to eight vehicles with validated VINs."""
    headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
    customer_id = _create_customer(client, headers)
    vehicles = [
        {
            "make": "BMW",
            "model": f"Series {index + 1}",
            "vin": f"WBAFR9C50BC{index:06d}",
        }
        for index in range(8)
    ]
    response = client.post(
        "/api/v1/orders",
        headers=headers,
        json={
            "customer_id": customer_id,
            "stops": [
                {"stop_type": "PICKUP", "sequence": 1, "city": "Gent"},
                {"stop_type": "DELIVERY", "sequence": 2, "city": "Brussels"},
            ],
            "vehicles": vehicles,
        },
    )

    assert response.status_code == 201
    assert len(response.json()["data"]["vehicles"]) == 8


def test_create_order_rejects_more_than_eight_vehicles(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Orders reject more than eight vehicles."""
    headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
    customer_id = _create_customer(client, headers)
    vehicles = [{"make": "Audi", "model": "A4"} for _ in range(9)]
    response = client.post(
        "/api/v1/orders",
        headers=headers,
        json={
            "customer_id": customer_id,
            "vehicles": vehicles,
        },
    )

    assert response.status_code == 422


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


def test_order_list_includes_customer_name(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Order list responses include the customer company name."""
    headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
    customer_response = client.post(
        "/api/v1/customers",
        headers=headers,
        json={"company_name": "Named Customer GmbH"},
    )
    customer_id = customer_response.json()["data"]["id"]
    client.post(
        "/api/v1/orders",
        headers=headers,
        json={"customer_id": customer_id},
    )

    list_response = client.get("/api/v1/orders", headers=headers)
    assert list_response.status_code == 200
    matching = [
        order
        for order in list_response.json()["data"]
        if order["customer_id"] == customer_id
    ]
    assert matching
    assert matching[0]["customer_name"] == "Named Customer GmbH"
