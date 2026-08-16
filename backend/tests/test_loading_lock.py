"""Loading lock and dispatcher reopen workflow tests."""

from fastapi.testclient import TestClient

VALID_VIN = "1HGBH41JXMN109186"


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _create_customer(client: TestClient, headers: dict[str, str]) -> str:
    response = client.post(
        "/api/v1/customers",
        headers=headers,
        json={"company_name": "Loading Lock Customer GmbH"},
    )
    assert response.status_code == 201
    return response.json()["data"]["id"]


def _create_driver(
    client: TestClient,
    admin_headers: dict[str, str],
    email: str,
) -> tuple[str, dict[str, str]]:
    user_response = client.post(
        "/api/v1/users",
        headers=admin_headers,
        json={
            "first_name": "Lock",
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
        headers=admin_headers,
        json={"user_id": user_response.json()["data"]["id"], "active": True},
    )
    assert driver_response.status_code == 201
    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Driver123!"},
    )
    return driver_response.json()["data"]["id"], _auth(login.json()["data"]["access_token"])


def _create_order_with_vehicle(
    client: TestClient,
    admin_headers: dict[str, str],
    driver_id: str,
) -> str:
    customer_id = _create_customer(client, admin_headers)
    order_response = client.post(
        "/api/v1/orders",
        headers=admin_headers,
        json={
            "customer_id": customer_id,
            "stops": [
                {
                    "stop_type": "PICKUP",
                    "sequence": 1,
                    "city": "Berlin",
                    "country": "DE",
                },
                {
                    "stop_type": "DELIVERY",
                    "sequence": 2,
                    "city": "Munich",
                    "country": "DE",
                },
            ],
            "vehicles": [
                {
                    "vin": VALID_VIN,
                    "make": "Honda",
                    "model": "Accord",
                }
            ],
        },
    )
    assert order_response.status_code == 201
    order_id = order_response.json()["data"]["id"]
    assign = client.post(
        f"/api/v1/orders/{order_id}/assign-driver",
        headers=admin_headers,
        json={"driver_id": driver_id},
    )
    assert assign.status_code == 200
    return order_id


def _advance_to_loaded(
    client: TestClient,
    order_id: str,
    driver_headers: dict[str, str],
) -> None:
    for step in ("accept", "arrive-pickup", "start-loading"):
        response = client.post(
            f"/api/v1/orders/{order_id}/{step}",
            headers=driver_headers,
        )
        assert response.status_code == 200, response.text

    vehicle_id = client.get(
        f"/api/v1/orders/{order_id}",
        headers=driver_headers,
    ).json()["data"]["vehicles"][0]["id"]
    verify = client.post(
        f"/api/v1/orders/{order_id}/vehicles/{vehicle_id}/verify-vin",
        headers=driver_headers,
        json={"vin": VALID_VIN},
    )
    assert verify.status_code == 200, verify.text

    generate = client.post(
        f"/api/v1/orders/{order_id}/cmr/generate",
        headers=driver_headers,
    )
    assert generate.status_code == 200, generate.text

    complete = client.post(
        f"/api/v1/orders/{order_id}/complete-loading",
        headers=driver_headers,
    )
    assert complete.status_code == 200, complete.text
    assert complete.json()["data"]["status"] == "LOADED"
    assert complete.json()["data"]["loading_locked"] is True


def test_loading_locked_blocks_vehicle_mutations(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """After finish loading, vehicle create/update/delete is blocked."""
    admin_headers = _auth(admin_tokens["access_token"])
    driver_id, driver_headers = _create_driver(client, admin_headers, "lock.driver@example.com")
    order_id = _create_order_with_vehicle(client, admin_headers, driver_id)
    _advance_to_loaded(client, order_id, driver_headers)

    create = client.post(
        f"/api/v1/orders/{order_id}/vehicles",
        headers=driver_headers,
        json={"vin": "2C3CDXBG9HH123456", "make": "Dodge", "model": "Charger"},
    )
    assert create.status_code == 422
    assert create.json()["error"]["code"] == "LOADING_LOCKED"

    vehicle_id = client.get(
        f"/api/v1/orders/{order_id}",
        headers=driver_headers,
    ).json()["data"]["vehicles"][0]["id"]

    update = client.put(
        f"/api/v1/vehicles/{vehicle_id}",
        headers=admin_headers,
        json={"vin": VALID_VIN, "make": "Honda", "model": "Updated"},
    )
    assert update.status_code == 422
    assert update.json()["error"]["code"] == "LOADING_LOCKED"

    delete = client.delete(f"/api/v1/vehicles/{vehicle_id}", headers=admin_headers)
    assert delete.status_code == 422
    assert delete.json()["error"]["code"] == "LOADING_LOCKED"


def test_driver_cannot_reopen_loading(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Drivers cannot reopen loading themselves."""
    admin_headers = _auth(admin_tokens["access_token"])
    driver_id, driver_headers = _create_driver(client, admin_headers, "lock.driver2@example.com")
    order_id = _create_order_with_vehicle(client, admin_headers, driver_id)
    _advance_to_loaded(client, order_id, driver_headers)

    response = client.post(
        f"/api/v1/orders/{order_id}/reopen-loading",
        headers=driver_headers,
        json={"reason": "Need to add another vehicle"},
    )
    assert response.status_code == 403


def test_dispatcher_reopen_loading_unlocks_vehicles(
    client: TestClient,
    admin_tokens: dict[str, str],
    db_session,
) -> None:
    """Dispatcher reopen returns order to LOADING and allows vehicle edits."""
    from app.audit.models import AuditLog

    admin_headers = _auth(admin_tokens["access_token"])
    driver_id, driver_headers = _create_driver(client, admin_headers, "lock.driver3@example.com")
    order_id = _create_order_with_vehicle(client, admin_headers, driver_id)
    _advance_to_loaded(client, order_id, driver_headers)

    reopen = client.post(
        f"/api/v1/orders/{order_id}/reopen-loading",
        headers=admin_headers,
        json={"reason": "Missing vehicle on manifest"},
    )
    assert reopen.status_code == 200, reopen.text
    payload = reopen.json()["data"]
    assert payload["status"] == "LOADING"
    assert payload["loading_locked"] is False

    create = client.post(
        f"/api/v1/orders/{order_id}/vehicles",
        headers=driver_headers,
        json={"vin": "2C3CDXBG9HH123456", "make": "Dodge", "model": "Charger"},
    )
    assert create.status_code == 201, create.text

    audit_entries = (
        db_session.query(AuditLog)
        .filter(
            AuditLog.entity_id == order_id,
            AuditLog.action == "LOADING_REOPENED",
        )
        .all()
    )
    assert len(audit_entries) == 1
    assert audit_entries[0].old_value == "LOADED"
    assert audit_entries[0].new_value == "LOADING|Missing vehicle on manifest"


def test_driver_cannot_start_loading_from_loaded(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Drivers cannot bypass dispatcher reopen by calling start-loading from LOADED."""
    admin_headers = _auth(admin_tokens["access_token"])
    driver_id, driver_headers = _create_driver(client, admin_headers, "lock.driver5@example.com")
    order_id = _create_order_with_vehicle(client, admin_headers, driver_id)
    _advance_to_loaded(client, order_id, driver_headers)

    response = client.post(
        f"/api/v1/orders/{order_id}/start-loading",
        headers=driver_headers,
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_ORDER_STATUS"


def test_reopen_loading_without_reason(
    client: TestClient,
    admin_tokens: dict[str, str],
    db_session,
) -> None:
    """Dispatcher can reopen loading without providing a reason."""
    from app.audit.models import AuditLog

    admin_headers = _auth(admin_tokens["access_token"])
    driver_id, driver_headers = _create_driver(client, admin_headers, "lock.driver6@example.com")
    order_id = _create_order_with_vehicle(client, admin_headers, driver_id)
    _advance_to_loaded(client, order_id, driver_headers)

    reopen = client.post(
        f"/api/v1/orders/{order_id}/reopen-loading",
        headers=admin_headers,
        json={"reason": ""},
    )
    assert reopen.status_code == 200, reopen.text
    assert reopen.json()["data"]["status"] == "LOADING"

    audit_entries = (
        db_session.query(AuditLog)
        .filter(
            AuditLog.entity_id == order_id,
            AuditLog.action == "LOADING_REOPENED",
        )
        .all()
    )
    assert len(audit_entries) == 1
    assert audit_entries[0].new_value == "LOADING"

