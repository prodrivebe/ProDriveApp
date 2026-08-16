"""Dispatcher order edit, stop/vehicle updates, and assignment persistence."""

from fastapi.testclient import TestClient

VALID_VIN = "1HGBH41JXMN109186"
VALID_VIN_2 = "2C3CDXBG9HH123456"


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _create_customer(client: TestClient, headers: dict[str, str]) -> str:
    response = client.post(
        "/api/v1/customers",
        headers=headers,
        json={"company_name": "Edit Test Customer"},
    )
    assert response.status_code == 201
    return response.json()["data"]["id"]


def _create_driver(client: TestClient, headers: dict[str, str], email: str) -> str:
    user_response = client.post(
        "/api/v1/users",
        headers=headers,
        json={
            "first_name": "Edit",
            "last_name": "Driver",
            "email": email,
            "password": "Driver123!",
            "role": "DRIVER",
            "is_active": True,
        },
    )
    assert user_response.status_code == 201
    driver_response = client.post(
        "/api/v1/drivers",
        headers=headers,
        json={"user_id": user_response.json()["data"]["id"], "active": True},
    )
    assert driver_response.status_code == 201
    return driver_response.json()["data"]["id"]


def _create_order(client: TestClient, headers: dict[str, str], customer_id: str) -> dict:
    response = client.post(
        "/api/v1/orders",
        headers=headers,
        json={
            "customer_id": customer_id,
            "notes": "Original notes",
            "customer_reference_numbers": ["REF-001"],
            "stops": [
                {
                    "stop_type": "PICKUP",
                    "sequence": 1,
                    "city": "Antwerp",
                    "address": "Dock 1",
                    "country": "BE",
                },
                {
                    "stop_type": "DELIVERY",
                    "sequence": 2,
                    "city": "Brussels",
                    "address": "Hub 2",
                    "country": "BE",
                },
            ],
            "vehicles": [
                {
                    "vin": VALID_VIN,
                    "make": "BMW",
                    "model": "X5",
                    "notes": "STOCK-100",
                }
            ],
        },
    )
    assert response.status_code == 201
    return response.json()["data"]


def test_dispatcher_can_edit_order_header_and_stops(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """PUT order and PUT stops persist customer, references, notes, and addresses."""
    headers = _auth(admin_tokens["access_token"])
    customer_id = _create_customer(client, headers)
    order = _create_order(client, headers, customer_id)

    update = client.put(
        f"/api/v1/orders/{order['id']}",
        headers=headers,
        json={
            "customer_id": customer_id,
            "notes": "Updated dispatcher notes",
            "customer_reference_numbers": ["REF-001", "REF-002"],
        },
    )
    assert update.status_code == 200, update.text
    assert update.json()["data"]["notes"] == "Updated dispatcher notes"
    assert update.json()["data"]["customer_reference_numbers"] == ["REF-001", "REF-002"]

    pickup_stop = next(stop for stop in order["stops"] if stop["stop_type"] == "PICKUP")
    delivery_stop = next(stop for stop in order["stops"] if stop["stop_type"] == "DELIVERY")

    pickup_update = client.put(
        f"/api/v1/stops/{pickup_stop['id']}",
        headers=headers,
        json={
            "stop_type": "PICKUP",
            "sequence": 1,
            "city": "Ghent",
            "address": "Port Lane 5",
            "country": "BE",
        },
    )
    assert pickup_update.status_code == 200, pickup_update.text

    delivery_update = client.put(
        f"/api/v1/stops/{delivery_stop['id']}",
        headers=headers,
        json={
            "stop_type": "DELIVERY",
            "sequence": 2,
            "city": "Liège",
            "address": "Rue Central 9",
            "country": "BE",
        },
    )
    assert delivery_update.status_code == 200, delivery_update.text

    reloaded = client.get(f"/api/v1/orders/{order['id']}", headers=headers)
    assert reloaded.status_code == 200
    data = reloaded.json()["data"]
    pickup = next(stop for stop in data["stops"] if stop["stop_type"] == "PICKUP")
    delivery = next(stop for stop in data["stops"] if stop["stop_type"] == "DELIVERY")
    assert pickup["city"] == "Ghent"
    assert pickup["address"] == "Port Lane 5"
    assert delivery["city"] == "Liège"
    assert delivery["address"] == "Rue Central 9"


def test_dispatcher_can_add_update_remove_vehicles(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Vehicle CRUD via dispatch endpoints respects the max vehicle limit."""
    headers = _auth(admin_tokens["access_token"])
    customer_id = _create_customer(client, headers)
    order = _create_order(client, headers, customer_id)
    order_id = order["id"]
    vehicle_id = order["vehicles"][0]["id"]

    update = client.put(
        f"/api/v1/vehicles/{vehicle_id}",
        headers=headers,
        json={
            "vin": VALID_VIN,
            "make": "BMW",
            "model": "X5 M",
            "notes": "STOCK-100-UPDATED",
        },
    )
    assert update.status_code == 200, update.text
    assert update.json()["data"]["model"] == "X5 M"
    assert update.json()["data"]["notes"] == "STOCK-100-UPDATED"

    create = client.post(
        f"/api/v1/orders/{order_id}/vehicles",
        headers=headers,
        json={"vin": VALID_VIN_2, "make": "Audi", "model": "A4", "notes": "STOCK-200"},
    )
    assert create.status_code == 201, create.text

    reloaded = client.get(f"/api/v1/orders/{order_id}", headers=headers)
    assert len(reloaded.json()["data"]["vehicles"]) == 2

    second_vehicle_id = next(
        vehicle["id"]
        for vehicle in reloaded.json()["data"]["vehicles"]
        if vehicle["id"] != vehicle_id
    )
    delete = client.delete(f"/api/v1/vehicles/{second_vehicle_id}", headers=headers)
    assert delete.status_code == 200

    final = client.get(f"/api/v1/orders/{order_id}", headers=headers)
    assert len(final.json()["data"]["vehicles"]) == 1


def test_edit_assignment_persists_truck_and_trailer(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Assign driver with truck and trailer; reload confirms persistence."""
    headers = _auth(admin_tokens["access_token"])
    customer_id = _create_customer(client, headers)
    driver_id = _create_driver(client, headers, "edit.assign@example.com")
    order = _create_order(client, headers, customer_id)

    truck_response = client.post(
        "/api/v1/trucks",
        headers=headers,
        json={"registration_number": "EDIT-TRK-1", "brand": "Scania", "model": "R", "active": True},
    )
    assert truck_response.status_code == 201
    truck_id = truck_response.json()["data"]["id"]

    trailer_response = client.post(
        "/api/v1/trailers",
        headers=headers,
        json={
            "registration_number": "EDIT-TRL-1",
            "trailer_type": "CAR_TRANSPORTER",
            "maximum_vehicle_count": 8,
            "active": True,
        },
    )
    assert trailer_response.status_code == 201
    trailer_id = trailer_response.json()["data"]["id"]

    assign = client.post(
        f"/api/v1/orders/{order['id']}/assign-driver",
        headers=headers,
        json={"driver_id": driver_id, "truck_id": truck_id, "trailer_id": trailer_id},
    )
    assert assign.status_code == 200, assign.text
    assigned = assign.json()["data"]
    assert assigned["assigned_truck_id"] == truck_id
    assert assigned["assigned_trailer_id"] == trailer_id

    reload = client.get(f"/api/v1/orders/{order['id']}", headers=headers)
    payload = reload.json()["data"]
    assert payload["assigned_driver_id"] == driver_id
    assert payload["assigned_truck_id"] == truck_id
    assert payload["assigned_trailer_id"] == trailer_id
