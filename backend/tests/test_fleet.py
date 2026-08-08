"""Fleet endpoint tests."""

import uuid

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit.models import AuditLog
from app.auth.security import hash_password
from app.common.enums import UserRole
from app.companies.models import Company, CompanySettings
from app.users.models import User


def _auth_headers(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


def _create_driver_user(
    client: TestClient,
    headers: dict[str, str],
    *,
    email: str = "fleet.driver@example.com",
    first_name: str = "Fleet",
    last_name: str = "Driver",
) -> str:
    """Create a driver user and return its id."""
    response = client.post(
        "/api/v1/users",
        headers=headers,
        json={
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "password": "Driver123!",
            "role": "DRIVER",
            "is_active": True,
        },
    )
    assert response.status_code == 201
    return response.json()["data"]["id"]


def _create_fleet_entities(
    client: TestClient,
    headers: dict[str, str],
    *,
    driver_email: str = "fleet.driver@example.com",
    truck_registration: str = "ABC123",
    trailer_registration: str = "TRL001",
) -> tuple[str, str, str]:
    """Create driver, truck, and trailer and return their ids."""
    user_id = _create_driver_user(client, headers, email=driver_email)
    driver_response = client.post(
        "/api/v1/drivers",
        headers=headers,
        json={"user_id": user_id, "phone": "+37060000001", "active": True},
    )
    assert driver_response.status_code == 201
    driver_id = driver_response.json()["data"]["id"]

    truck_response = client.post(
        "/api/v1/trucks",
        headers=headers,
        json={
            "registration_number": truck_registration,
            "brand": "Volvo",
            "active": True,
        },
    )
    assert truck_response.status_code == 201
    truck_id = truck_response.json()["data"]["id"]

    trailer_response = client.post(
        "/api/v1/trailers",
        headers=headers,
        json={
            "registration_number": trailer_registration,
            "maximum_vehicle_count": 5,
            "active": True,
        },
    )
    assert trailer_response.status_code == 201
    trailer_id = trailer_response.json()["data"]["id"]
    return driver_id, truck_id, trailer_id


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
    response = client.get("/api/v1/drivers", headers=_auth_headers(access_token))

    assert response.status_code == 200
    assert response.json()["success"] is True


def test_admin_can_create_driver_profile(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Admin can create a driver profile for a driver user."""
    headers = _auth_headers(admin_tokens["access_token"])
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
    headers = _auth_headers(admin_tokens["access_token"])
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
    headers = _auth_headers(admin_tokens["access_token"])
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

    get_response = client.get(f"/api/v1/trucks/{truck_id}", headers=headers)
    assert get_response.status_code == 200
    assert get_response.json()["data"]["registration_number"] == "ABC123"

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
    headers = _auth_headers(admin_tokens["access_token"])
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
    headers = _auth_headers(admin_tokens["access_token"])
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
    trailer_id = response.json()["data"]["id"]
    get_response = client.get(f"/api/v1/trailers/{trailer_id}", headers=headers)
    assert get_response.status_code == 200
    assert get_response.json()["data"]["maximum_vehicle_count"] == 5


def test_invalid_trailer_capacity_is_rejected(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Unsupported trailer capacity values are rejected."""
    headers = _auth_headers(admin_tokens["access_token"])
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
    headers = _auth_headers(admin_tokens["access_token"])
    _create_fleet_entities(
        client,
        headers,
        truck_registration="OV001",
        trailer_registration="OV002",
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
    headers = _auth_headers(admin_tokens["access_token"])
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


def test_admin_can_soft_delete_driver(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Admin can soft delete a driver profile."""
    headers = _auth_headers(admin_tokens["access_token"])
    user_id = _create_driver_user(client, headers, email="delete.driver@example.com")
    create_response = client.post(
        "/api/v1/drivers",
        headers=headers,
        json={"user_id": user_id, "active": True},
    )
    driver_id = create_response.json()["data"]["id"]
    delete_response = client.delete(f"/api/v1/drivers/{driver_id}", headers=headers)

    assert delete_response.status_code == 200
    list_response = client.get("/api/v1/drivers", headers=headers)
    assert list_response.json()["meta"]["pagination"]["total"] == 0


def test_driver_search_by_name(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Driver list search matches linked user name."""
    headers = _auth_headers(admin_tokens["access_token"])
    user_id = _create_driver_user(
        client,
        headers,
        email="search.driver@example.com",
        first_name="Unique",
        last_name="SearchName",
    )
    client.post(
        "/api/v1/drivers",
        headers=headers,
        json={"user_id": user_id, "active": True},
    )

    response = client.get(
        "/api/v1/drivers",
        headers=headers,
        params={"search": "SearchName"},
    )
    assert response.status_code == 200
    assert response.json()["meta"]["pagination"]["total"] == 1


def test_duplicate_truck_registration_is_rejected(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Truck registration numbers must be unique within a company."""
    headers = _auth_headers(admin_tokens["access_token"])
    payload = {"registration_number": "DUP123", "active": True}
    first = client.post("/api/v1/trucks", headers=headers, json=payload)
    second = client.post("/api/v1/trucks", headers=headers, json=payload)

    assert first.status_code == 201
    assert second.status_code == 422
    assert second.json()["error"]["code"] == "REGISTRATION_ALREADY_EXISTS"


def test_admin_can_create_fleet_assignment(
    client: TestClient,
    admin_tokens: dict[str, str],
    db_session: Session,
) -> None:
    """Admin can create a standing fleet assignment."""
    headers = _auth_headers(admin_tokens["access_token"])
    driver_id, truck_id, trailer_id = _create_fleet_entities(
        client,
        headers,
        driver_email="assign.driver@example.com",
        truck_registration="ASN001",
        trailer_registration="ASN002",
    )

    response = client.post(
        "/api/v1/fleet/assignments",
        headers=headers,
        json={
            "driver_id": driver_id,
            "truck_id": truck_id,
            "trailer_id": trailer_id,
        },
    )

    assert response.status_code == 201
    body = response.json()["data"]
    assert body["driver_id"] == driver_id
    assert body["truck_id"] == truck_id
    assert body["trailer_id"] == trailer_id
    assert body["active"] is True

    logs = list(db_session.scalars(select(AuditLog)).all())
    assert any(log.action == "ASSIGNMENT_CREATED" for log in logs)


def test_duplicate_assignment_is_rejected(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Only one active assignment is allowed per driver, truck, or trailer."""
    headers = _auth_headers(admin_tokens["access_token"])
    driver_id, truck_id, trailer_id = _create_fleet_entities(
        client,
        headers,
        driver_email="dup.driver1@example.com",
        truck_registration="DUPTRK1",
        trailer_registration="DUPTRL1",
    )
    client.post(
        "/api/v1/fleet/assignments",
        headers=headers,
        json={
            "driver_id": driver_id,
            "truck_id": truck_id,
            "trailer_id": trailer_id,
        },
    )

    user_id_2 = _create_driver_user(client, headers, email="dup.driver2@example.com")
    driver_2 = client.post(
        "/api/v1/drivers",
        headers=headers,
        json={"user_id": user_id_2, "active": True},
    ).json()["data"]["id"]

    duplicate_truck = client.post(
        "/api/v1/fleet/assignments",
        headers=headers,
        json={
            "driver_id": driver_2,
            "truck_id": truck_id,
            "trailer_id": trailer_id,
        },
    )
    assert duplicate_truck.status_code == 422
    assert duplicate_truck.json()["error"]["code"] == "TRUCK_ALREADY_ASSIGNED"


def test_admin_can_remove_fleet_assignment(
    client: TestClient,
    admin_tokens: dict[str, str],
    db_session: Session,
) -> None:
    """Admin can deactivate a fleet assignment."""
    headers = _auth_headers(admin_tokens["access_token"])
    driver_id, truck_id, trailer_id = _create_fleet_entities(
        client,
        headers,
        driver_email="remove.driver@example.com",
        truck_registration="RMV001",
        trailer_registration="RMV002",
    )
    create_response = client.post(
        "/api/v1/fleet/assignments",
        headers=headers,
        json={
            "driver_id": driver_id,
            "truck_id": truck_id,
            "trailer_id": trailer_id,
        },
    )
    assignment_id = create_response.json()["data"]["id"]

    delete_response = client.delete(
        f"/api/v1/fleet/assignments/{assignment_id}",
        headers=headers,
    )
    assert delete_response.status_code == 200
    assert delete_response.json()["data"]["active"] is False
    assert delete_response.json()["data"]["unassigned_at"] is not None

    logs = list(db_session.scalars(select(AuditLog)).all())
    assert any(log.action == "ASSIGNMENT_REMOVED" for log in logs)


def test_driver_can_read_own_assignment(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Driver can read their active fleet assignment."""
    admin_headers = _auth_headers(admin_tokens["access_token"])
    driver_id, truck_id, trailer_id = _create_fleet_entities(
        client,
        admin_headers,
        driver_email="ownassign.driver@example.com",
        truck_registration="OWN001",
        trailer_registration="OWN002",
    )
    client.post(
        "/api/v1/fleet/assignments",
        headers=admin_headers,
        json={
            "driver_id": driver_id,
            "truck_id": truck_id,
            "trailer_id": trailer_id,
        },
    )

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "ownassign.driver@example.com", "password": "Driver123!"},
    )
    driver_headers = _auth_headers(login_response.json()["data"]["access_token"])
    response = client.get("/api/v1/fleet/assignments/me", headers=driver_headers)

    assert response.status_code == 200
    assert response.json()["data"]["driver_id"] == driver_id


def test_driver_cannot_create_assignment(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Drivers cannot create fleet assignments."""
    admin_headers = _auth_headers(admin_tokens["access_token"])
    driver_id, truck_id, trailer_id = _create_fleet_entities(
        client,
        admin_headers,
        driver_email="nodispatch.driver@example.com",
        truck_registration="ND001",
        trailer_registration="ND002",
    )
    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "nodispatch.driver@example.com", "password": "Driver123!"},
    )
    driver_headers = _auth_headers(login_response.json()["data"]["access_token"])
    response = client.post(
        "/api/v1/fleet/assignments",
        headers=driver_headers,
        json={
            "driver_id": driver_id,
            "truck_id": truck_id,
            "trailer_id": trailer_id,
        },
    )

    assert response.status_code == 403


def test_cross_company_driver_access_returns_not_found(
    client: TestClient,
    admin_tokens: dict[str, str],
    db_session: Session,
) -> None:
    """Cross-company access to fleet resources returns 404."""
    headers = _auth_headers(admin_tokens["access_token"])
    user_id = _create_driver_user(client, headers, email="tenant.driver@example.com")
    driver_id = client.post(
        "/api/v1/drivers",
        headers=headers,
        json={"user_id": user_id, "active": True},
    ).json()["data"]["id"]

    other_company = Company(name="Other Transport")
    db_session.add(other_company)
    db_session.commit()
    db_session.refresh(other_company)
    db_session.add(CompanySettings(company_id=other_company.id))
    other_admin = User(
        company_id=other_company.id,
        first_name="Other",
        last_name="Admin",
        email="other.admin@example.com",
        password_hash=hash_password("OtherAdmin123!"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(other_admin)
    db_session.commit()

    other_login = client.post(
        "/api/v1/auth/login",
        json={"email": "other.admin@example.com", "password": "OtherAdmin123!"},
    )
    other_headers = _auth_headers(other_login.json()["data"]["access_token"])
    response = client.get(f"/api/v1/drivers/{driver_id}", headers=other_headers)

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "DRIVER_NOT_FOUND"


def test_fleet_mutations_create_audit_logs(
    client: TestClient,
    admin_tokens: dict[str, str],
    db_session: Session,
) -> None:
    """Fleet CRUD operations write audit records."""
    headers = _auth_headers(admin_tokens["access_token"])
    user_id = _create_driver_user(client, headers, email="audit.driver@example.com")
    driver_id = client.post(
        "/api/v1/drivers",
        headers=headers,
        json={"user_id": user_id, "active": True},
    ).json()["data"]["id"]
    truck_id = client.post(
        "/api/v1/trucks",
        headers=headers,
        json={"registration_number": "AUD001", "active": True},
    ).json()["data"]["id"]
    trailer_payload = {
        "registration_number": "AUD002",
        "maximum_vehicle_count": 8,
        "active": True,
    }
    trailer_id = client.post(
        "/api/v1/trailers",
        headers=headers,
        json=trailer_payload,
    ).json()["data"]["id"]

    client.put(
        f"/api/v1/drivers/{driver_id}",
        headers=headers,
        json={"phone": "+37061111111", "active": True},
    )
    client.put(
        f"/api/v1/trucks/{truck_id}",
        headers=headers,
        json={"registration_number": "AUD001", "active": True},
    )
    client.put(
        f"/api/v1/trailers/{trailer_id}",
        headers=headers,
        json=trailer_payload,
    )
    client.delete(f"/api/v1/drivers/{driver_id}", headers=headers)
    client.delete(f"/api/v1/trucks/{truck_id}", headers=headers)
    client.delete(f"/api/v1/trailers/{trailer_id}", headers=headers)

    actions = {log.action for log in db_session.scalars(select(AuditLog)).all()}
    assert "DRIVER_CREATED" in actions
    assert "DRIVER_UPDATED" in actions
    assert "DRIVER_DELETED" in actions
    assert "TRUCK_CREATED" in actions
    assert "TRUCK_UPDATED" in actions
    assert "TRUCK_DELETED" in actions
    assert "TRAILER_CREATED" in actions
    assert "TRAILER_UPDATED" in actions
    assert "TRAILER_DELETED" in actions


def test_assignment_with_unknown_driver_returns_not_found(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Assignment creation validates that the driver exists in the company."""
    headers = _auth_headers(admin_tokens["access_token"])
    _, truck_id, trailer_id = _create_fleet_entities(
        client,
        headers,
        driver_email="known.driver@example.com",
        truck_registration="VAL001",
        trailer_registration="VAL002",
    )
    response = client.post(
        "/api/v1/fleet/assignments",
        headers=headers,
        json={
            "driver_id": str(uuid.uuid4()),
            "truck_id": truck_id,
            "trailer_id": trailer_id,
        },
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "DRIVER_NOT_FOUND"
