"""Sprint 4 order management domain tests."""

import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.audit.models import AuditLog
from app.auth.security import hash_password
from app.common.enums import UserRole
from app.companies.models import Company, CompanySettings
from app.users.models import User


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _create_customer(client: TestClient, headers: dict[str, str], name: str = "Order Customer") -> str:
    response = client.post(
        "/api/v1/customers",
        headers=headers,
        json={"company_name": name},
    )
    assert response.status_code == 201
    return response.json()["data"]["id"]


def _create_order(
    client: TestClient,
    headers: dict[str, str],
    customer_id: str,
    **extra: object,
) -> dict:
    payload = {"customer_id": customer_id, **extra}
    response = client.post("/api/v1/orders", headers=headers, json=payload)
    assert response.status_code == 201
    return response.json()["data"]


def _create_driver_user(
    client: TestClient,
    headers: dict[str, str],
    email: str = "driver.orders@example.com",
) -> tuple[str, str]:
    user_response = client.post(
        "/api/v1/users",
        headers=headers,
        json={
            "first_name": "Order",
            "last_name": "Driver",
            "email": email,
            "password": "Driver123!",
            "role": "DRIVER",
            "is_active": True,
        },
    )
    assert user_response.status_code == 201
    user_id = user_response.json()["data"]["id"]
    driver_response = client.post(
        "/api/v1/drivers",
        headers=headers,
        json={"user_id": user_id, "active": True},
    )
    assert driver_response.status_code == 201
    return user_id, driver_response.json()["data"]["id"]


def _driver_headers(client: TestClient, email: str, password: str = "Driver123!") -> dict[str, str]:
    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login.status_code == 200
    return _auth(login.json()["data"]["access_token"])


def test_order_crud_list_get_update_delete(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Admin can list, get, update, and soft delete orders."""
    headers = _auth(admin_tokens["access_token"])
    customer_id = _create_customer(client, headers)
    order = _create_order(client, headers, customer_id, notes="Initial notes")

    list_response = client.get("/api/v1/orders", headers=headers)
    assert list_response.status_code == 200
    assert list_response.json()["meta"]["pagination"]["total"] >= 1

    get_response = client.get(f"/api/v1/orders/{order['id']}", headers=headers)
    assert get_response.status_code == 200
    assert get_response.json()["data"]["notes"] == "Initial notes"

    update_response = client.put(
        f"/api/v1/orders/{order['id']}",
        headers=headers,
        json={
            "customer_id": customer_id,
            "notes": "Updated notes",
            "status": "READY",
        },
    )
    assert update_response.status_code == 200
    assert update_response.json()["data"]["status"] == "READY"
    assert update_response.json()["data"]["notes"] == "Updated notes"

    delete_response = client.delete(f"/api/v1/orders/{order['id']}", headers=headers)
    assert delete_response.status_code == 200

    missing_response = client.get(f"/api/v1/orders/{order['id']}", headers=headers)
    assert missing_response.status_code == 404


def test_multi_stop_order_with_sequence_validation(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Orders support multiple stops with unique sequence numbers."""
    headers = _auth(admin_tokens["access_token"])
    customer_id = _create_customer(client, headers)
    order = _create_order(client, headers, customer_id)

    for sequence, city in [(1, "Paris"), (2, "Lyon"), (3, "Marseille")]:
        response = client.post(
            f"/api/v1/orders/{order['id']}/stops",
            headers=headers,
            json={
                "stop_type": "PICKUP" if sequence == 1 else "DELIVERY",
                "sequence": sequence,
                "city": city,
            },
        )
        assert response.status_code == 201

    duplicate_response = client.post(
        f"/api/v1/orders/{order['id']}/stops",
        headers=headers,
        json={"stop_type": "DELIVERY", "sequence": 2, "city": "Duplicate"},
    )
    assert duplicate_response.status_code == 422
    assert duplicate_response.json()["error"]["code"] == "DUPLICATE_STOP_SEQUENCE"

    stops_response = client.get(f"/api/v1/orders/{order['id']}/stops", headers=headers)
    assert stops_response.status_code == 200
    assert len(stops_response.json()["data"]) == 3


def test_multi_vehicle_order_with_stop_links(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Orders support multiple vehicles linked to pickup and delivery stops."""
    headers = _auth(admin_tokens["access_token"])
    customer_id = _create_customer(client, headers)
    order = _create_order(
        client,
        headers,
        customer_id,
        stops=[
            {"stop_type": "PICKUP", "sequence": 1, "city": "Berlin"},
            {"stop_type": "DELIVERY", "sequence": 2, "city": "Munich"},
        ],
    )
    pickup_id = order["stops"][0]["id"]
    delivery_id = order["stops"][1]["id"]

    first_vehicle = client.post(
        f"/api/v1/orders/{order['id']}/vehicles",
        headers=headers,
        json={
            "make": "BMW",
            "model": "3 Series",
            "pickup_stop_id": pickup_id,
            "delivery_stop_id": delivery_id,
        },
    )
    assert first_vehicle.status_code == 201

    second_vehicle = client.post(
        f"/api/v1/orders/{order['id']}/vehicles",
        headers=headers,
        json={"make": "Audi", "model": "A6"},
    )
    assert second_vehicle.status_code == 201

    vehicles_response = client.get(
        f"/api/v1/orders/{order['id']}/vehicles",
        headers=headers,
    )
    assert vehicles_response.status_code == 200
    assert len(vehicles_response.json()["data"]) == 2


def test_invalid_vehicle_stop_link_rejected(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Vehicle pickup/delivery stops must belong to the order and match types."""
    headers = _auth(admin_tokens["access_token"])
    customer_id = _create_customer(client, headers)
    order = _create_order(
        client,
        headers,
        customer_id,
        stops=[
            {"stop_type": "PICKUP", "sequence": 1, "city": "Hamburg"},
            {"stop_type": "DELIVERY", "sequence": 2, "city": "Cologne"},
        ],
    )
    delivery_id = order["stops"][1]["id"]

    response = client.post(
        f"/api/v1/orders/{order['id']}/vehicles",
        headers=headers,
        json={
            "make": "VW",
            "model": "Golf",
            "pickup_stop_id": delivery_id,
        },
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_PICKUP_STOP"


def test_timeline_records_order_lifecycle_events(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Timeline automatically records create, stop, vehicle, and status events."""
    headers = _auth(admin_tokens["access_token"])
    customer_id = _create_customer(client, headers)
    order = _create_order(client, headers, customer_id)

    stop_response = client.post(
        f"/api/v1/orders/{order['id']}/stops",
        headers=headers,
        json={"stop_type": "PICKUP", "sequence": 1, "city": "Rome"},
    )
    stop_id = stop_response.json()["data"]["id"]

    vehicle_response = client.post(
        f"/api/v1/orders/{order['id']}/vehicles",
        headers=headers,
        json={"make": "Fiat", "model": "500"},
    )
    vehicle_id = vehicle_response.json()["data"]["id"]

    client.put(
        f"/api/v1/orders/{order['id']}",
        headers=headers,
        json={"customer_id": customer_id, "status": "READY"},
    )

    client.delete(f"/api/v1/stops/{stop_id}", headers=headers)
    client.delete(f"/api/v1/vehicles/{vehicle_id}", headers=headers)

    timeline_response = client.get(
        f"/api/v1/orders/{order['id']}/timeline",
        headers=headers,
    )
    events = [entry["event_type"] for entry in timeline_response.json()["data"]]
    assert "ORDER_CREATED" in events
    assert "STOP_ADDED" in events
    assert "VEHICLE_ADDED" in events
    assert "STATUS_CHANGED" in events
    assert "STOP_REMOVED" in events
    assert "VEHICLE_REMOVED" in events


def test_stop_and_vehicle_mutations_create_audit_logs(
    client: TestClient,
    admin_tokens: dict[str, str],
    db_session: Session,
) -> None:
    """Stop and vehicle mutations write audit records."""
    headers = _auth(admin_tokens["access_token"])
    customer_id = _create_customer(client, headers)
    order = _create_order(client, headers, customer_id)

    stop_response = client.post(
        f"/api/v1/orders/{order['id']}/stops",
        headers=headers,
        json={"stop_type": "PICKUP", "sequence": 1, "city": "Vienna"},
    )
    stop_id = stop_response.json()["data"]["id"]

    vehicle_response = client.post(
        f"/api/v1/orders/{order['id']}/vehicles",
        headers=headers,
        json={"make": "Skoda", "model": "Octavia"},
    )
    vehicle_id = vehicle_response.json()["data"]["id"]

    client.put(
        f"/api/v1/stops/{stop_id}",
        headers=headers,
        json={"stop_type": "PICKUP", "sequence": 1, "city": "Salzburg"},
    )
    client.put(
        f"/api/v1/vehicles/{vehicle_id}",
        headers=headers,
        json={"make": "Skoda", "model": "Superb"},
    )
    client.delete(f"/api/v1/stops/{stop_id}", headers=headers)
    client.delete(f"/api/v1/vehicles/{vehicle_id}", headers=headers)

    actions = {
        row.action
        for row in db_session.query(AuditLog).filter(
            AuditLog.entity.in_(["order_stop", "order_vehicle"])
        )
    }
    assert "ORDER_STOP_ADDED" in actions
    assert "ORDER_STOP_UPDATED" in actions
    assert "ORDER_STOP_REMOVED" in actions
    assert "ORDER_VEHICLE_ADDED" in actions
    assert "ORDER_VEHICLE_UPDATED" in actions
    assert "ORDER_VEHICLE_REMOVED" in actions


def test_cross_company_order_access_returns_not_found(
    client: TestClient,
    admin_tokens: dict[str, str],
    db_session: Session,
) -> None:
    """Cross-company order access returns 404."""
    headers = _auth(admin_tokens["access_token"])
    customer_id = _create_customer(client, headers)
    order = _create_order(client, headers, customer_id)

    other_company = Company(name="Other Orders Co")
    db_session.add(other_company)
    db_session.commit()
    db_session.refresh(other_company)
    db_session.add(CompanySettings(company_id=other_company.id))
    other_admin = User(
        company_id=other_company.id,
        first_name="Other",
        last_name="Admin",
        email="other.orders@example.com",
        password_hash=hash_password("OtherAdmin123!"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(other_admin)
    db_session.commit()

    other_login = client.post(
        "/api/v1/auth/login",
        json={"email": "other.orders@example.com", "password": "OtherAdmin123!"},
    )
    other_headers = _auth(other_login.json()["data"]["access_token"])

    response = client.get(f"/api/v1/orders/{order['id']}", headers=other_headers)
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "ORDER_NOT_FOUND"


def test_driver_cannot_create_orders(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Drivers cannot create orders."""
    admin_headers = _auth(admin_tokens["access_token"])
    customer_id = _create_customer(client, admin_headers)
    _create_driver_user(client, admin_headers, email="perm.driver@example.com")
    driver_headers = _driver_headers(client, "perm.driver@example.com")

    response = client.post(
        "/api/v1/orders",
        headers=driver_headers,
        json={"customer_id": customer_id},
    )
    assert response.status_code == 403


def test_invalid_status_transition_rejected(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Invalid status transitions are rejected."""
    headers = _auth(admin_tokens["access_token"])
    customer_id = _create_customer(client, headers)
    order = _create_order(client, headers, customer_id)

    response = client.put(
        f"/api/v1/orders/{order['id']}",
        headers=headers,
        json={"customer_id": customer_id, "status": "IN_TRANSIT"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_ORDER_STATUS"


def test_completed_order_cannot_be_edited(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Completed orders reject stop and vehicle mutations."""
    headers = _auth(admin_tokens["access_token"])
    customer_id = _create_customer(client, headers)
    _, driver_id = _create_driver_user(client, headers, email="complete.driver@example.com")
    order = _create_order(client, headers, customer_id)

    client.put(
        f"/api/v1/orders/{order['id']}",
        headers=headers,
        json={"customer_id": customer_id, "status": "READY"},
    )
    client.post(
        f"/api/v1/orders/{order['id']}/assign-driver",
        headers=headers,
        json={"driver_id": driver_id},
    )

    driver_headers = _driver_headers(client, "complete.driver@example.com")
    for path in (
        "accept",
        "arrive-pickup",
        "start-loading",
        "complete-loading",
        "start-transit",
        "arrive-delivery",
        "start-delivery",
        "complete-delivery",
    ):
        if path == "complete-loading":
            generate = client.post(
                f"/api/v1/orders/{order['id']}/cmr/generate",
                headers=driver_headers,
            )
            assert generate.status_code == 200, generate.text
        step = client.post(
            f"/api/v1/orders/{order['id']}/{path}",
            headers=driver_headers,
        )
        assert step.status_code == 200

    stop_response = client.post(
        f"/api/v1/orders/{order['id']}/stops",
        headers=headers,
        json={"stop_type": "PICKUP", "sequence": 1, "city": "Late stop"},
    )
    assert stop_response.status_code == 422
    assert stop_response.json()["error"]["code"] == "ORDER_NOT_EDITABLE"


def test_wizard_order_records_stop_and_vehicle_timeline(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Creating an order with wizard payload records stop and vehicle timeline events."""
    headers = _auth(admin_tokens["access_token"])
    customer_id = _create_customer(client, headers)
    order = _create_order(
        client,
        headers,
        customer_id,
        stops=[
            {"stop_type": "PICKUP", "sequence": 1, "city": "Oslo"},
            {"stop_type": "DELIVERY", "sequence": 2, "city": "Stockholm"},
        ],
        vehicles=[{"make": "Volvo", "model": "XC90"}, {"make": "Saab", "model": "9-3"}],
    )

    timeline_response = client.get(
        f"/api/v1/orders/{order['id']}/timeline",
        headers=headers,
    )
    events = [entry["event_type"] for entry in timeline_response.json()["data"]]
    assert events.count("STOP_ADDED") == 2
    assert events.count("VEHICLE_ADDED") == 2
    assert "ORDER_CREATED" in events


def test_random_uuid_order_returns_not_found(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Unknown order IDs return 404."""
    headers = _auth(admin_tokens["access_token"])
    response = client.get(f"/api/v1/orders/{uuid.uuid4()}", headers=headers)
    assert response.status_code == 404
