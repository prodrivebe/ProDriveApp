"""Fleet endpoint tests."""

from fastapi.testclient import TestClient


def _create_driver_user(client: TestClient, headers: dict[str, str]) -> str:
    """Create a driver user and return its id."""
    response = client.post(
        "/api/v1/users",
        headers=headers,
        json={
            "first_name": "Fleet",
            "last_name": "Driver",
            "email": "fleet.driver@example.com",
            "password": "Driver123!",
            "role": "DRIVER",
            "is_active": True,
        },
    )
    assert response.status_code == 201
    return response.json()["data"]["id"]


def test_dispatcher_can_list_drivers(client: TestClient) -> None:
    """Dispatcher can access fleet driver endpoints."""
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "dispatcher@example.com",
            "password": "Dispatch123!",
        },
    )
    access_token = login_response.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get("/api/v1/drivers", headers=headers)

    assert response.status_code == 200
    assert response.json()["success"] is True


def test_admin_can_create_driver_profile(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Admin can create a driver profile for a driver user."""
    headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
    user_id = _create_driver_user(client, headers)
    response = client.post(
        "/api/v1/drivers",
        headers=headers,
        json={
            "user_id": user_id,
            "phone": "+37060000001",
            "driving_license": "DL-123456",
            "active": True,
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["data"]["user_id"] == user_id
    assert body["data"]["phone"] == "+37060000001"


def test_cannot_create_duplicate_driver_profile(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Creating a second profile for the same user is rejected."""
    headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
    user_id = _create_driver_user(client, headers)
    payload = {
        "user_id": user_id,
        "phone": "+37060000002",
        "active": True,
    }
    first_response = client.post("/api/v1/drivers", headers=headers, json=payload)
    second_response = client.post("/api/v1/drivers", headers=headers, json=payload)

    assert first_response.status_code == 201
    assert second_response.status_code == 422
    assert second_response.json()["error"]["code"] == "DRIVER_ALREADY_EXISTS"


def test_admin_can_create_and_update_truck(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Admin can create and update a truck."""
    headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
    create_response = client.post(
        "/api/v1/trucks",
        headers=headers,
        json={
            "registration_number": "ABC123",
            "brand": "Volvo",
            "model": "FH16",
            "capacity": 40,
            "active": True,
        },
    )
    assert create_response.status_code == 201
    truck_id = create_response.json()["data"]["id"]

    update_response = client.put(
        f"/api/v1/trucks/{truck_id}",
        headers=headers,
        json={
            "registration_number": "ABC123",
            "brand": "Volvo",
            "model": "FH16 Updated",
            "capacity": 40,
            "active": True,
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["data"]["model"] == "FH16 Updated"


def test_admin_can_delete_truck(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Admin can soft delete a truck."""
    headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
    create_response = client.post(
        "/api/v1/trucks",
        headers=headers,
        json={
            "registration_number": "DEL999",
            "brand": "Scania",
            "active": True,
        },
    )
    truck_id = create_response.json()["data"]["id"]
    delete_response = client.delete(f"/api/v1/trucks/{truck_id}", headers=headers)

    assert delete_response.status_code == 200
    list_response = client.get("/api/v1/trucks", headers=headers)
    assert list_response.json()["meta"]["pagination"]["total"] == 0


def test_admin_can_create_trailer_with_valid_capacity(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Admin can create a trailer with supported capacity."""
    headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
    response = client.post(
        "/api/v1/trailers",
        headers=headers,
        json={
            "registration_number": "TRL001",
            "manufacturer": "Krone",
            "maximum_vehicle_count": 5,
            "active": True,
        },
    )

    assert response.status_code == 201
    assert response.json()["data"]["maximum_vehicle_count"] == 5


def test_invalid_trailer_capacity_is_rejected(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Unsupported trailer capacity values are rejected."""
    headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
    response = client.post(
        "/api/v1/trailers",
        headers=headers,
        json={
            "registration_number": "TRL002",
            "maximum_vehicle_count": 4,
            "active": True,
        },
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_TRAILER_CAPACITY"


def test_fleet_overview_returns_counts(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Fleet overview aggregates driver, truck, and trailer counts."""
    headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
    user_id = _create_driver_user(client, headers)
    client.post(
        "/api/v1/drivers",
        headers=headers,
        json={"user_id": user_id, "active": True},
    )
    client.post(
        "/api/v1/trucks",
        headers=headers,
        json={"registration_number": "OV001", "active": True},
    )
    client.post(
        "/api/v1/trailers",
        headers=headers,
        json={"registration_number": "OV002", "maximum_vehicle_count": 8, "active": True},
    )

    response = client.get("/api/v1/fleet/overview", headers=headers)

    assert response.status_code == 200
    overview = response.json()["data"]
    assert overview["drivers"]["total"] == 1
    assert overview["trucks"]["total"] == 1
    assert overview["trailers"]["total"] == 1


def test_driver_orders_returns_empty_when_unassigned(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Driver orders endpoint returns an empty paginated list when none assigned."""
    headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
    user_id = _create_driver_user(client, headers)
    create_response = client.post(
        "/api/v1/drivers",
        headers=headers,
        json={"user_id": user_id, "active": True},
    )
    driver_id = create_response.json()["data"]["id"]
    response = client.get(f"/api/v1/drivers/{driver_id}/orders", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"] == []
    assert body["meta"]["pagination"]["total"] == 0
