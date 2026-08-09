"""Sprint 6 vehicle execution and evidence workflow tests."""

import io

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.auth.security import hash_password
from app.common.enums import UserRole
from app.companies.models import Company, CompanySettings
from app.users.models import User

MINIMAL_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
    b"\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
    b"\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01"
    b"\x0d\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)
VALID_VIN = "1HGBH41JXMN109186"
UPDATED_VIN = "5YJSA1E14HF000001"
REQUIRED_PHOTO_TYPES = ("FRONT", "REAR", "LEFT", "RIGHT")


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _create_customer(client: TestClient, headers: dict[str, str]) -> str:
    response = client.post(
        "/api/v1/customers",
        headers=headers,
        json={"company_name": "Execution Customer GmbH"},
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
            "first_name": "Execution",
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


def _create_assigned_order(
    client: TestClient,
    admin_headers: dict[str, str],
    driver_id: str,
    *,
    vin: str | None = VALID_VIN,
) -> tuple[str, str]:
    customer_id = _create_customer(client, admin_headers)
    vehicle_payload: dict = {"make": "BMW", "model": "X3"}
    if vin is not None:
        vehicle_payload["vin"] = vin
    order = client.post(
        "/api/v1/orders",
        headers=admin_headers,
        json={
            "customer_id": customer_id,
            "stops": [
                {"stop_type": "PICKUP", "sequence": 1, "city": "Hamburg"},
                {"stop_type": "DELIVERY", "sequence": 2, "city": "Berlin"},
            ],
            "vehicles": [vehicle_payload],
        },
    )
    assert order.status_code == 201
    order_id = order.json()["data"]["id"]
    vehicle_id = order.json()["data"]["vehicles"][0]["id"]
    client.put(
        f"/api/v1/orders/{order_id}",
        headers=admin_headers,
        json={"customer_id": customer_id, "status": "READY"},
    )
    assign = client.post(
        f"/api/v1/orders/{order_id}/assign-driver",
        headers=admin_headers,
        json={"driver_id": driver_id},
    )
    assert assign.status_code == 200
    return order_id, vehicle_id


def _upload_required_photos(
    client: TestClient,
    headers: dict[str, str],
    order_id: str,
    vehicle_id: str,
) -> None:
    for photo_type in REQUIRED_PHOTO_TYPES:
        response = client.post(
            f"/api/v1/orders/{order_id}/vehicles/{vehicle_id}/photos",
            headers=headers,
            files={"file": (f"{photo_type.lower()}.png", io.BytesIO(MINIMAL_PNG), "image/png")},
            data={"photo_type": photo_type},
        )
        assert response.status_code == 201, photo_type


def _fulfill_checklist(
    client: TestClient,
    headers: dict[str, str],
    order_id: str,
    vehicle_id: str,
    *,
    vin: str = VALID_VIN,
) -> None:
    verify = client.post(
        f"/api/v1/orders/{order_id}/vehicles/{vehicle_id}/verify-vin",
        headers=headers,
        json={"vin": vin},
    )
    assert verify.status_code == 200
    _upload_required_photos(client, headers, order_id, vehicle_id)
    document = client.post(
        f"/api/v1/orders/{order_id}/documents",
        headers=headers,
        files={"file": ("cmr.png", io.BytesIO(MINIMAL_PNG), "image/png")},
        data={"document_type": "CMR"},
    )
    assert document.status_code == 201


def _advance_to_delivery_ready(
    client: TestClient,
    driver_headers: dict[str, str],
    order_id: str,
) -> None:
    for step in (
        "accept",
        "arrive-pickup",
        "start-loading",
        "complete-loading",
        "start-transit",
        "arrive-delivery",
        "start-delivery",
    ):
        response = client.post(
            f"/api/v1/orders/{order_id}/{step}",
            headers=driver_headers,
        )
        assert response.status_code == 200, step


def test_driver_can_verify_vin_and_read_history(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Driver verifies VIN and immutable history is preserved."""
    admin_headers = _auth(admin_tokens["access_token"])
    driver_id, driver_headers = _create_driver(
        client,
        admin_headers,
        "vin.verify@example.com",
    )
    order_id, vehicle_id = _create_assigned_order(client, admin_headers, driver_id)

    verify = client.post(
        f"/api/v1/orders/{order_id}/vehicles/{vehicle_id}/verify-vin",
        headers=driver_headers,
        json={"vin": VALID_VIN},
    )
    assert verify.status_code == 200
    assert verify.json()["data"]["verified_vin"] == VALID_VIN

    update = client.put(
        f"/api/v1/orders/{order_id}/vehicles/{vehicle_id}/vin",
        headers=driver_headers,
        json={"vin": UPDATED_VIN},
    )
    assert update.status_code == 200
    assert update.json()["data"]["verified_vin"] == UPDATED_VIN

    history = client.get(
        f"/api/v1/orders/{order_id}/vehicles/{vehicle_id}/vin-history",
        headers=driver_headers,
    )
    assert history.status_code == 200
    entries = history.json()["data"]
    assert len(entries) == 2
    assert entries[0]["verified_vin"] == UPDATED_VIN
    assert entries[1]["verified_vin"] == VALID_VIN


def test_invalid_vin_is_rejected(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Invalid VIN format returns validation error."""
    admin_headers = _auth(admin_tokens["access_token"])
    driver_id, driver_headers = _create_driver(
        client,
        admin_headers,
        "vin.invalid@example.com",
    )
    order_id, vehicle_id = _create_assigned_order(client, admin_headers, driver_id, vin=None)

    response = client.post(
        f"/api/v1/orders/{order_id}/vehicles/{vehicle_id}/verify-vin",
        headers=driver_headers,
        json={"vin": "INVALID-VIN"},
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_VIN"


def test_photo_upload_validation_and_delete(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Photo uploads validate type and support deletion."""
    admin_headers = _auth(admin_tokens["access_token"])
    driver_id, driver_headers = _create_driver(
        client,
        admin_headers,
        "photo.upload@example.com",
    )
    order_id, vehicle_id = _create_assigned_order(client, admin_headers, driver_id)

    invalid = client.post(
        f"/api/v1/orders/{order_id}/vehicles/{vehicle_id}/photos",
        headers=driver_headers,
        files={"file": ("notes.txt", io.BytesIO(b"not-an-image"), "text/plain")},
        data={"photo_type": "FRONT"},
    )
    assert invalid.status_code == 422
    assert invalid.json()["error"]["code"] == "INVALID_PHOTO_TYPE"

    upload = client.post(
        f"/api/v1/orders/{order_id}/vehicles/{vehicle_id}/photos",
        headers=driver_headers,
        files={"file": ("front.png", io.BytesIO(MINIMAL_PNG), "image/png")},
        data={"photo_type": "FRONT"},
    )
    assert upload.status_code == 201
    photo_id = upload.json()["data"]["id"]

    listed = client.get(
        f"/api/v1/orders/{order_id}/vehicles/{vehicle_id}/photos",
        headers=driver_headers,
    )
    assert listed.status_code == 200
    assert len(listed.json()["data"]) == 1

    deleted = client.delete(f"/api/v1/photos/{photo_id}", headers=admin_headers)
    assert deleted.status_code == 200


def test_damage_crud_with_photo_attachment(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Driver can report damage and attach vehicle photos."""
    admin_headers = _auth(admin_tokens["access_token"])
    driver_id, driver_headers = _create_driver(
        client,
        admin_headers,
        "damage.crud@example.com",
    )
    order_id, vehicle_id = _create_assigned_order(client, admin_headers, driver_id)

    photo = client.post(
        f"/api/v1/orders/{order_id}/vehicles/{vehicle_id}/photos",
        headers=driver_headers,
        files={"file": ("damage.png", io.BytesIO(MINIMAL_PNG), "image/png")},
        data={"photo_type": "DAMAGE"},
    )
    assert photo.status_code == 201
    photo_id = photo.json()["data"]["id"]

    create = client.post(
        f"/api/v1/orders/{order_id}/vehicles/{vehicle_id}/damage",
        headers=driver_headers,
        json={
            "damage_type": "SCRATCH",
            "severity": "MINOR",
            "description": "Scratch on rear bumper",
            "location": "Rear bumper",
            "photo_ids": [photo_id],
        },
    )
    assert create.status_code == 201
    damage_id = create.json()["data"]["id"]
    assert create.json()["data"]["photo_ids"] == [photo_id]

    listed = client.get(
        f"/api/v1/orders/{order_id}/vehicles/{vehicle_id}/damage",
        headers=driver_headers,
    )
    assert listed.status_code == 200
    assert len(listed.json()["data"]) == 1

    updated = client.put(
        f"/api/v1/damage/{damage_id}",
        headers=admin_headers,
        json={
            "damage_type": "DENT",
            "severity": "MODERATE",
            "description": "Updated damage description",
            "location": "Rear bumper",
            "photo_ids": [photo_id],
        },
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["damage_type"] == "DENT"

    deleted = client.delete(f"/api/v1/damage/{damage_id}", headers=admin_headers)
    assert deleted.status_code == 200


def test_cmr_document_versioning(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Uploading CMR creates new versions without deleting previous ones."""
    admin_headers = _auth(admin_tokens["access_token"])
    order_id, _ = _create_assigned_order(
        client,
        admin_headers,
        _create_driver(client, admin_headers, "cmr.version@example.com")[0],
    )

    first = client.post(
        f"/api/v1/orders/{order_id}/documents",
        headers=admin_headers,
        files={"file": ("cmr-v1.png", io.BytesIO(MINIMAL_PNG), "image/png")},
        data={"document_type": "CMR"},
    )
    assert first.status_code == 201
    assert first.json()["data"]["version"] == 1

    second = client.post(
        f"/api/v1/orders/{order_id}/documents",
        headers=admin_headers,
        files={"file": ("cmr-v2.png", io.BytesIO(MINIMAL_PNG), "image/png")},
        data={"document_type": "CMR"},
    )
    assert second.status_code == 201
    assert second.json()["data"]["version"] == 2

    listed = client.get(f"/api/v1/orders/{order_id}/documents", headers=admin_headers)
    assert listed.status_code == 200
    versions = sorted(item["version"] for item in listed.json()["data"])
    assert versions == [1, 2]


def test_completion_checklist_and_enforced_order_completion(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Completion validation reports missing items and blocks incomplete orders."""
    admin_headers = _auth(admin_tokens["access_token"])
    driver_id, driver_headers = _create_driver(
        client,
        admin_headers,
        "checklist@example.com",
    )
    order_id, vehicle_id = _create_assigned_order(client, admin_headers, driver_id)
    _advance_to_delivery_ready(client, driver_headers, order_id)

    checklist = client.get(
        f"/api/v1/orders/{order_id}/completion-checklist",
        headers=driver_headers,
    )
    assert checklist.status_code == 200
    assert checklist.json()["data"]["can_complete"] is False
    assert "vins_verified" in checklist.json()["data"]["missing_items"]

    blocked = client.post(
        f"/api/v1/orders/{order_id}/complete-delivery",
        headers=driver_headers,
    )
    assert blocked.status_code == 422
    assert blocked.json()["error"]["code"] == "CHECKLIST_INCOMPLETE"

    _fulfill_checklist(client, driver_headers, order_id, vehicle_id)

    validated = client.post(
        f"/api/v1/orders/{order_id}/validate-completion",
        headers=driver_headers,
    )
    assert validated.status_code == 200
    validation_data = validated.json()["data"]
    assert "vins_verified" in validation_data["completed_items"]
    assert "documents_uploaded" in validation_data["completed_items"]
    assert validation_data["delivery_completed"] is False

    completed = client.post(
        f"/api/v1/orders/{order_id}/complete-delivery",
        headers=driver_headers,
    )
    assert completed.status_code == 200
    assert completed.json()["data"]["status"] == "COMPLETED"

    final_checklist = client.get(
        f"/api/v1/orders/{order_id}/completion-checklist",
        headers=driver_headers,
    )
    assert final_checklist.status_code == 200
    assert final_checklist.json()["data"]["can_complete"] is True
    assert final_checklist.json()["data"]["completion_percentage"] == 100


def test_unassigned_driver_cannot_verify_vin(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Drivers cannot execute evidence actions on unassigned orders."""
    admin_headers = _auth(admin_tokens["access_token"])
    assigned_driver_id, _ = _create_driver(
        client,
        admin_headers,
        "assigned.driver@example.com",
    )
    _, other_driver_headers = _create_driver(
        client,
        admin_headers,
        "other.driver@example.com",
    )
    order_id, vehicle_id = _create_assigned_order(
        client,
        admin_headers,
        assigned_driver_id,
    )

    response = client.post(
        f"/api/v1/orders/{order_id}/vehicles/{vehicle_id}/verify-vin",
        headers=other_driver_headers,
        json={"vin": VALID_VIN},
    )
    assert response.status_code == 403


def test_cross_company_access_returns_not_found(
    client: TestClient,
    admin_tokens: dict[str, str],
    db_session: Session,
) -> None:
    """Cross-company order access returns 404."""
    admin_headers = _auth(admin_tokens["access_token"])
    driver_id, driver_headers = _create_driver(
        client,
        admin_headers,
        "tenant.a@example.com",
    )
    order_id, vehicle_id = _create_assigned_order(client, admin_headers, driver_id)

    other_company = Company(name="Other Transport")
    db_session.add(other_company)
    db_session.commit()
    db_session.refresh(other_company)
    db_session.add(CompanySettings(company_id=other_company.id))
    other_user = User(
        company_id=other_company.id,
        first_name="Other",
        last_name="Admin",
        email="other-admin@example.com",
        password_hash=hash_password("OtherAdmin123!"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(other_user)
    db_session.commit()

    other_login = client.post(
        "/api/v1/auth/login",
        json={"email": "other-admin@example.com", "password": "OtherAdmin123!"},
    )
    other_headers = _auth(other_login.json()["data"]["access_token"])

    response = client.get(
        f"/api/v1/orders/{order_id}/vehicles/{vehicle_id}/photos",
        headers=other_headers,
    )
    assert response.status_code == 404
