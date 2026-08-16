"""Sprint 5 driver workflow tests."""

import base64
import io
import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.audit.models import AuditLog
from app.auth.security import hash_password
from app.common.enums import StopType, UserRole
from app.companies.models import Company, CompanySettings
from app.notifications.models import Notification
from app.orders.models import OrderStop
from app.users.models import User

MINIMAL_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
    b"\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
    b"\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01"
    b"\x0d\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)
VALID_VIN = "1HGBH41JXMN109186"

FULL_WORKFLOW = (
    "accept",
    "arrive-pickup",
    "start-loading",
    "complete-loading",
    "start-transit",
    "arrive-delivery",
    "finish-delivery",
    "complete-delivery",
)


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _create_customer(client: TestClient, headers: dict[str, str]) -> str:
    response = client.post(
        "/api/v1/customers",
        headers=headers,
        json={"company_name": "Workflow Customer GmbH"},
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
            "first_name": "Workflow",
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
    with_stops: bool = True,
) -> str:
    customer_id = _create_customer(client, admin_headers)
    payload: dict = {"customer_id": customer_id}
    if with_stops:
        payload["stops"] = [
            {"stop_type": "PICKUP", "sequence": 1, "city": "Hamburg"},
            {"stop_type": "DELIVERY", "sequence": 2, "city": "Berlin"},
        ]
        payload["vehicles"] = [{"make": "BMW", "model": "X3"}]
    order = client.post("/api/v1/orders", headers=admin_headers, json=payload)
    assert order.status_code == 201
    order_id = order.json()["data"]["id"]
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
    return order_id


def _verify_order_vehicles(
    client: TestClient,
    headers: dict[str, str],
    order_id: str,
) -> None:
    order = client.get(f"/api/v1/orders/{order_id}", headers=headers)
    assert order.status_code == 200
    for vehicle in order.json()["data"]["vehicles"]:
        verify = client.post(
            f"/api/v1/orders/{order_id}/vehicles/{vehicle['id']}/verify-vin",
            headers=headers,
            json={"vin": vehicle.get("vin") or VALID_VIN},
        )
        assert verify.status_code == 200


def _upload_signed_cmr(
    client: TestClient,
    headers: dict[str, str],
    order_id: str,
) -> None:
    response = client.post(
        f"/api/v1/orders/{order_id}/documents",
        headers=headers,
        files={"file": ("signed-cmr.png", io.BytesIO(MINIMAL_PNG), "image/png")},
        data={"document_type": "CMR"},
    )
    assert response.status_code == 201, response.text


def _fulfill_execution_checklist(
    client: TestClient,
    headers: dict[str, str],
    order_id: str,
) -> None:
    """Generate CMR draft required before finishing loading."""
    generate = client.post(
        f"/api/v1/orders/{order_id}/cmr/generate",
        headers=headers,
    )
    assert generate.status_code == 200, generate.text


def _generate_cmr(
    client: TestClient,
    headers: dict[str, str],
    order_id: str,
) -> None:
    _fulfill_execution_checklist(client, headers, order_id)


def test_full_driver_workflow_transitions(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Driver can execute the full operational workflow."""
    admin_headers = _auth(admin_tokens["access_token"])
    driver_id, driver_headers = _create_driver(
        client,
        admin_headers,
        "full.workflow@example.com",
    )
    order_id = _create_assigned_order(client, admin_headers, driver_id)

    for step in FULL_WORKFLOW:
        if step == "start-loading":
            response = client.post(
                f"/api/v1/orders/{order_id}/{step}",
                headers=driver_headers,
            )
            assert response.status_code == 200, step
            _verify_order_vehicles(client, driver_headers, order_id)
            _generate_cmr(client, driver_headers, order_id)
            continue
        if step == "finish-delivery":
            _upload_signed_cmr(client, driver_headers, order_id)
        response = client.post(
            f"/api/v1/orders/{order_id}/{step}",
            headers=driver_headers,
        )
        assert response.status_code == 200, step

    final = client.get(f"/api/v1/orders/{order_id}", headers=admin_headers)
    assert final.json()["data"]["status"] == "COMPLETED"


def test_invalid_workflow_transition_rejected(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Workflow rejects transitions from the wrong state."""
    admin_headers = _auth(admin_tokens["access_token"])
    driver_id, driver_headers = _create_driver(
        client,
        admin_headers,
        "invalid.workflow@example.com",
    )
    order_id = _create_assigned_order(client, admin_headers, driver_id)

    response = client.post(
        f"/api/v1/orders/{order_id}/start-loading",
        headers=driver_headers,
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_ORDER_STATUS"


def test_accept_arrived_start_finish_loading_integration(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Accept -> Arrived -> Start Loading -> Finish Loading returns updated order."""
    admin_headers = _auth(admin_tokens["access_token"])
    driver_id, driver_headers = _create_driver(
        client,
        admin_headers,
        "loading.integration@example.com",
    )
    order_id = _create_assigned_order(client, admin_headers, driver_id)

    accept = client.post(
        f"/api/v1/orders/{order_id}/accept",
        headers=driver_headers,
    )
    assert accept.status_code == 200
    assert accept.json()["data"]["status"] == "ACCEPTED"

    arrived = client.post(
        f"/api/v1/orders/{order_id}/arrive-pickup",
        headers=driver_headers,
    )
    assert arrived.status_code == 200
    assert arrived.json()["data"]["status"] == "ARRIVED_PICKUP"

    start = client.post(
        f"/api/v1/orders/{order_id}/start-loading",
        headers=driver_headers,
    )
    assert start.status_code == 200, start.text
    start_payload = start.json()["data"]
    assert start_payload["id"] == order_id
    assert start_payload["status"] == "LOADING"

    _verify_order_vehicles(client, driver_headers, order_id)
    _generate_cmr(client, driver_headers, order_id)

    finish = client.post(
        f"/api/v1/orders/{order_id}/complete-loading",
        headers=driver_headers,
    )
    assert finish.status_code == 200, finish.text
    assert finish.json()["data"]["status"] == "LOADED"


def _advance_to_arrived_delivery(
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
    ):
        if step == "complete-loading":
            _verify_order_vehicles(client, driver_headers, order_id)
            generate = client.post(
                f"/api/v1/orders/{order_id}/cmr/generate",
                headers=driver_headers,
            )
            assert generate.status_code == 200, generate.text
        response = client.post(
            f"/api/v1/orders/{order_id}/{step}",
            headers=driver_headers,
        )
        assert response.status_code == 200, step


def test_arrived_delivery_requires_signed_cmr_before_finish(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Driver must upload signed CMR before finishing delivery."""
    admin_headers = _auth(admin_tokens["access_token"])
    driver_id, driver_headers = _create_driver(
        client,
        admin_headers,
        "delivery.cmr.complete@example.com",
    )
    order_id = _create_assigned_order(client, admin_headers, driver_id)
    _advance_to_arrived_delivery(client, driver_headers, order_id)

    order = client.get(f"/api/v1/orders/{order_id}", headers=driver_headers)
    assert order.status_code == 200
    assert order.json()["data"]["status"] == "ARRIVED_DELIVERY"

    blocked = client.post(
        f"/api/v1/orders/{order_id}/finish-delivery",
        headers=driver_headers,
    )
    assert blocked.status_code == 422
    assert blocked.json()["error"]["code"] == "CMR_REQUIRED"

    _upload_signed_cmr(client, driver_headers, order_id)

    finished = client.post(
        f"/api/v1/orders/{order_id}/finish-delivery",
        headers=driver_headers,
    )
    assert finished.status_code == 200, finished.text
    assert finished.json()["data"]["status"] == "DELIVERING"

    completed = client.post(
        f"/api/v1/orders/{order_id}/complete-delivery",
        headers=driver_headers,
    )
    assert completed.status_code == 200, completed.text
    assert completed.json()["data"]["status"] == "COMPLETED"

    refreshed = client.get(f"/api/v1/orders/{order_id}", headers=admin_headers)
    assert refreshed.json()["data"]["status"] == "COMPLETED"

    final_stops = client.get(f"/api/v1/orders/{order_id}/stops", headers=admin_headers)
    final_delivery = next(
        stop for stop in final_stops.json()["data"] if stop["stop_type"] == "DELIVERY"
    )
    assert final_delivery["progress_status"] == "COMPLETED"


def test_start_loading_with_duplicate_stop_sequences(
    client: TestClient,
    admin_tokens: dict[str, str],
    db_session: Session,
) -> None:
    """Start loading still targets pickup when legacy data shares stop sequence."""
    admin_headers = _auth(admin_tokens["access_token"])
    driver_id, driver_headers = _create_driver(
        client,
        admin_headers,
        "duplicate.sequence@example.com",
    )
    order_id = _create_assigned_order(client, admin_headers, driver_id)

    delivery_stop = (
        db_session.query(OrderStop)
        .filter(
            OrderStop.order_id == uuid.UUID(order_id),
            OrderStop.stop_type == StopType.DELIVERY,
        )
        .one()
    )
    delivery_stop.sequence = 1
    db_session.commit()

    client.post(f"/api/v1/orders/{order_id}/accept", headers=driver_headers)
    client.post(f"/api/v1/orders/{order_id}/arrive-pickup", headers=driver_headers)

    start = client.post(
        f"/api/v1/orders/{order_id}/start-loading",
        headers=driver_headers,
    )
    assert start.status_code == 200, start.text
    assert start.json()["data"]["status"] == "LOADING"

    stops = client.get(f"/api/v1/orders/{order_id}/stops", headers=admin_headers)
    pickup = next(
        stop for stop in stops.json()["data"] if stop["stop_type"] == "PICKUP"
    )
    assert pickup["progress_status"] == "LOADING"


def test_unauthorized_driver_cannot_execute_workflow(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Only the assigned driver may execute workflow actions."""
    admin_headers = _auth(admin_tokens["access_token"])
    assigned_driver_id, _ = _create_driver(
        client,
        admin_headers,
        "assigned.workflow@example.com",
    )
    _, other_driver_headers = _create_driver(
        client,
        admin_headers,
        "other.workflow@example.com",
    )
    order_id = _create_assigned_order(client, admin_headers, assigned_driver_id)

    response = client.post(
        f"/api/v1/orders/{order_id}/accept",
        headers=other_driver_headers,
    )
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_dispatcher_can_override_workflow(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Admins and dispatchers may execute workflow actions."""
    admin_headers = _auth(admin_tokens["access_token"])
    driver_id, _ = _create_driver(client, admin_headers, "override.workflow@example.com")
    order_id = _create_assigned_order(client, admin_headers, driver_id)

    response = client.post(
        f"/api/v1/orders/{order_id}/accept",
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "ACCEPTED"


def test_workflow_creates_timeline_and_audit_entries(
    client: TestClient,
    admin_tokens: dict[str, str],
    db_session: Session,
) -> None:
    """Workflow actions create timeline entries and audited status changes."""
    admin_headers = _auth(admin_tokens["access_token"])
    driver_id, driver_headers = _create_driver(
        client,
        admin_headers,
        "audit.workflow@example.com",
    )
    order_id = _create_assigned_order(client, admin_headers, driver_id)

    client.post(f"/api/v1/orders/{order_id}/accept", headers=driver_headers)
    client.post(f"/api/v1/orders/{order_id}/arrive-pickup", headers=driver_headers)

    timeline = client.get(f"/api/v1/orders/{order_id}/timeline", headers=admin_headers)
    events = [entry["event_type"] for entry in timeline.json()["data"]]
    assert "DRIVER_ACCEPTED" in events
    assert "ARRIVED_PICKUP" in events
    assert "STATUS_CHANGED" in events

    audit_actions = {
        row.action
        for row in db_session.query(AuditLog).filter(AuditLog.entity == "order")
    }
    assert "DRIVER_ACCEPTED" in audit_actions
    assert "ARRIVED_PICKUP" in audit_actions


def test_workflow_creates_notification_records(
    client: TestClient,
    admin_tokens: dict[str, str],
    db_session: Session,
) -> None:
    """Workflow milestones create in-app notification records."""
    admin_headers = _auth(admin_tokens["access_token"])
    driver_id, driver_headers = _create_driver(
        client,
        admin_headers,
        "notify.workflow@example.com",
    )
    order_id = _create_assigned_order(client, admin_headers, driver_id)

    client.post(f"/api/v1/orders/{order_id}/accept", headers=driver_headers)
    client.post(f"/api/v1/orders/{order_id}/arrive-pickup", headers=driver_headers)
    client.post(f"/api/v1/orders/{order_id}/start-loading", headers=driver_headers)
    _verify_order_vehicles(client, driver_headers, order_id)
    _generate_cmr(client, driver_headers, order_id)
    client.post(f"/api/v1/orders/{order_id}/complete-loading", headers=driver_headers)

    types = {row.type for row in db_session.query(Notification)}
    assert "ORDER_ACCEPTED" in types
    assert "PICKUP_ARRIVED" in types
    assert "LOADING_COMPLETED" in types


def test_stop_progress_is_tracked_through_workflow(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Stop progress and timestamps update through pickup workflow."""
    admin_headers = _auth(admin_tokens["access_token"])
    driver_id, driver_headers = _create_driver(
        client,
        admin_headers,
        "stops.workflow@example.com",
    )
    order_id = _create_assigned_order(client, admin_headers, driver_id)

    client.post(f"/api/v1/orders/{order_id}/accept", headers=driver_headers)
    client.post(f"/api/v1/orders/{order_id}/arrive-pickup", headers=driver_headers)

    stops = client.get(f"/api/v1/orders/{order_id}/stops", headers=admin_headers)
    pickup = stops.json()["data"][0]
    assert pickup["progress_status"] == "ARRIVED"
    assert pickup["arrival_time"] is not None

    client.post(f"/api/v1/orders/{order_id}/start-loading", headers=driver_headers)
    stops = client.get(f"/api/v1/orders/{order_id}/stops", headers=admin_headers)
    assert stops.json()["data"][0]["progress_status"] == "LOADING"

    _verify_order_vehicles(client, driver_headers, order_id)
    _generate_cmr(client, driver_headers, order_id)
    client.post(f"/api/v1/orders/{order_id}/complete-loading", headers=driver_headers)
    stops = client.get(f"/api/v1/orders/{order_id}/stops", headers=admin_headers)
    completed_pickup = stops.json()["data"][0]
    assert completed_pickup["progress_status"] == "COMPLETED"
    assert completed_pickup["departure_time"] is not None


def test_driver_current_order_endpoint(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Current-order endpoint returns order context for the driver home screen."""
    admin_headers = _auth(admin_tokens["access_token"])
    driver_id, driver_headers = _create_driver(
        client,
        admin_headers,
        "current.workflow@example.com",
    )
    order_id = _create_assigned_order(client, admin_headers, driver_id)
    client.post(f"/api/v1/orders/{order_id}/accept", headers=driver_headers)

    response = client.get("/api/v1/drivers/me/current-order", headers=driver_headers)
    assert response.status_code == 200
    body = response.json()["data"]
    assert body["order"]["id"] == order_id
    assert body["workflow_status"] == "ACCEPTED"
    assert body["current_stop"] is not None
    assert len(body["vehicles"]) == 1
    assert "pickup" in body["next_required_action"].lower()


def test_completed_order_blocks_workflow(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Completed orders cannot continue through the workflow."""
    admin_headers = _auth(admin_tokens["access_token"])
    driver_id, driver_headers = _create_driver(
        client,
        admin_headers,
        "completed.workflow@example.com",
    )
    order_id = _create_assigned_order(client, admin_headers, driver_id)

    for step in FULL_WORKFLOW:
        if step == "start-loading":
            client.post(f"/api/v1/orders/{order_id}/{step}", headers=driver_headers)
            _verify_order_vehicles(client, driver_headers, order_id)
            _generate_cmr(client, driver_headers, order_id)
            continue
        if step == "finish-delivery":
            _upload_signed_cmr(client, driver_headers, order_id)
        client.post(f"/api/v1/orders/{order_id}/{step}", headers=driver_headers)

    response = client.post(
        f"/api/v1/orders/{order_id}/accept",
        headers=driver_headers,
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "ORDER_NOT_EDITABLE"


def test_cross_company_workflow_returns_not_found(
    client: TestClient,
    admin_tokens: dict[str, str],
    db_session: Session,
) -> None:
    """Cross-company workflow access returns 404."""
    admin_headers = _auth(admin_tokens["access_token"])
    driver_id, driver_headers = _create_driver(
        client,
        admin_headers,
        "tenant.workflow@example.com",
    )
    order_id = _create_assigned_order(client, admin_headers, driver_id)

    other_company = Company(name="Other Workflow Co")
    db_session.add(other_company)
    db_session.commit()
    db_session.refresh(other_company)
    db_session.add(CompanySettings(company_id=other_company.id))
    other_admin = User(
        company_id=other_company.id,
        first_name="Other",
        last_name="Admin",
        email="other.workflow@example.com",
        password_hash=hash_password("OtherAdmin123!"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(other_admin)
    db_session.commit()

    other_login = client.post(
        "/api/v1/auth/login",
        json={"email": "other.workflow@example.com", "password": "OtherAdmin123!"},
    )
    other_headers = _auth(other_login.json()["data"]["access_token"])

    response = client.post(
        f"/api/v1/orders/{order_id}/accept",
        headers=other_headers,
    )
    assert response.status_code == 404


def test_reject_order_returns_to_ready(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Rejecting an assignment clears the driver and creates notifications."""
    admin_headers = _auth(admin_tokens["access_token"])
    driver_id, driver_headers = _create_driver(
        client,
        admin_headers,
        "reject.workflow@example.com",
    )
    order_id = _create_assigned_order(client, admin_headers, driver_id)

    response = client.post(
        f"/api/v1/orders/{order_id}/reject",
        headers=driver_headers,
    )
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "READY"
    assert response.json()["data"]["assigned_driver_id"] is None

    timeline = client.get(f"/api/v1/orders/{order_id}/timeline", headers=admin_headers)
    events = [entry["event_type"] for entry in timeline.json()["data"]]
    assert "DRIVER_REJECTED" in events


def test_multi_pickup_requires_multiple_cycles(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Multiple pickup stops require repeating the pickup cycle."""
    admin_headers = _auth(admin_tokens["access_token"])
    driver_id, driver_headers = _create_driver(
        client,
        admin_headers,
        "multi.pickup@example.com",
    )
    customer_id = _create_customer(client, admin_headers)
    order = client.post(
        "/api/v1/orders",
        headers=admin_headers,
        json={
            "customer_id": customer_id,
            "stops": [
                {"stop_type": "PICKUP", "sequence": 1, "city": "A"},
                {"stop_type": "PICKUP", "sequence": 2, "city": "B"},
                {"stop_type": "DELIVERY", "sequence": 3, "city": "C"},
            ],
            "vehicles": [{"make": "Audi", "model": "A4", "vin": VALID_VIN}],
        },
    )
    order_id = order.json()["data"]["id"]
    client.put(
        f"/api/v1/orders/{order_id}",
        headers=admin_headers,
        json={"customer_id": customer_id, "status": "READY"},
    )
    client.post(
        f"/api/v1/orders/{order_id}/assign-driver",
        headers=admin_headers,
        json={"driver_id": driver_id},
    )

    client.post(f"/api/v1/orders/{order_id}/accept", headers=driver_headers)
    client.post(f"/api/v1/orders/{order_id}/arrive-pickup", headers=driver_headers)
    client.post(f"/api/v1/orders/{order_id}/start-loading", headers=driver_headers)
    _verify_order_vehicles(client, driver_headers, order_id)
    _generate_cmr(client, driver_headers, order_id)
    complete_first = client.post(
        f"/api/v1/orders/{order_id}/complete-loading",
        headers=driver_headers,
    )
    assert complete_first.json()["data"]["status"] == "ACCEPTED"

    client.post(f"/api/v1/orders/{order_id}/arrive-pickup", headers=driver_headers)
    client.post(f"/api/v1/orders/{order_id}/start-loading", headers=driver_headers)
    _verify_order_vehicles(client, driver_headers, order_id)
    _generate_cmr(client, driver_headers, order_id)
    complete_second = client.post(
        f"/api/v1/orders/{order_id}/complete-loading",
        headers=driver_headers,
    )
    assert complete_second.json()["data"]["status"] == "LOADED"


def test_driver_can_add_vehicle_during_loading(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Assigned drivers can register vehicles while loading."""
    admin_headers = _auth(admin_tokens["access_token"])
    driver_id, driver_headers = _create_driver(
        client,
        admin_headers,
        "loading.vehicle@example.com",
    )
    order_id = _create_assigned_order(
        client,
        admin_headers,
        driver_id,
        with_stops=True,
    )

    client.post(f"/api/v1/orders/{order_id}/accept", headers=driver_headers)
    client.post(f"/api/v1/orders/{order_id}/arrive-pickup", headers=driver_headers)

    too_early = client.post(
        f"/api/v1/orders/{order_id}/vehicles",
        headers=driver_headers,
        json={"make": "Blocked", "model": "Car", "vin": VALID_VIN},
    )
    assert too_early.status_code == 422
    assert too_early.json()["error"]["code"] == "INVALID_ORDER_STATUS"

    client.post(f"/api/v1/orders/{order_id}/start-loading", headers=driver_headers)
    create = client.post(
        f"/api/v1/orders/{order_id}/vehicles",
        headers=driver_headers,
        json={"make": "Mercedes", "model": "C-Class", "vin": VALID_VIN},
    )
    assert create.status_code == 201
    vehicle_id = create.json()["data"]["id"]
    verify = client.post(
        f"/api/v1/orders/{order_id}/vehicles/{vehicle_id}/verify-vin",
        headers=driver_headers,
        json={"vin": VALID_VIN},
    )
    assert verify.status_code == 200

    dispatcher_create = client.post(
        f"/api/v1/orders/{order_id}/vehicles",
        headers=admin_headers,
        json={"make": "BMW", "model": "X5", "vin": "5UXCR6C05M9D12345"},
    )
    assert dispatcher_create.status_code == 201
