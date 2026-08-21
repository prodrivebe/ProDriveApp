"""CMR generation, reference numbers, and pickup loading workflow tests."""

import io

from fastapi.testclient import TestClient
from pypdf import PdfReader


MINIMAL_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
    b"\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
    b"\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01"
    b"\x0d\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)


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


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _create_customer(client: TestClient, headers: dict[str, str]) -> str:
    response = client.post(
        "/api/v1/customers",
        headers=headers,
        json={"company_name": "CMR Reference Customer GmbH"},
    )
    assert response.status_code == 201
    return response.json()["data"]["id"]


def _create_order_with_references(
    client: TestClient,
    headers: dict[str, str],
) -> str:
    customer_id = _create_customer(client, headers)
    response = client.post(
        "/api/v1/orders",
        headers=headers,
        json={
            "customer_id": customer_id,
            "customer_reference_numbers": ["31MGBE4985", "31MGBE5029"],
            "planned_pickup_date": "2026-08-12",
            "planned_delivery_date": "2026-08-14",
            "stops": [
                {
                    "stop_type": "PICKUP",
                    "sequence": 1,
                    "company_name": "Pickup Co",
                    "city": "Antwerp",
                    "country": "BE",
                },
                {
                    "stop_type": "DELIVERY",
                    "sequence": 2,
                    "company_name": "Delivery Co",
                    "city": "Brussels",
                    "country": "BE",
                },
            ],
            "vehicles": [{"make": "MG", "model": "MG3", "vin": "LSJWP4396TZ174225"}],
        },
    )
    assert response.status_code == 201, response.text
    payload = response.json()["data"]
    assert payload["customer_reference_numbers"] == ["31MGBE4985", "31MGBE5029"]
    return payload["id"]


def _create_driver(
    client: TestClient,
    admin_headers: dict[str, str],
    email: str,
) -> tuple[str, dict[str, str]]:
    user_response = client.post(
        "/api/v1/users",
        headers=admin_headers,
        json={
            "first_name": "CMR",
            "last_name": "Driver",
            "email": email,
            "password": "DriverPass123!",
            "role": "DRIVER",
            "is_active": True,
        },
    )
    assert user_response.status_code == 201, user_response.text
    driver_response = client.post(
        "/api/v1/drivers",
        headers=admin_headers,
        json={
            "user_id": user_response.json()["data"]["id"],
            "phone": "+32470000001",
            "active": True,
        },
    )
    assert driver_response.status_code == 201, driver_response.text
    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "DriverPass123!"},
    )
    assert login.status_code == 200
    return driver_response.json()["data"]["id"], _auth(login.json()["data"]["access_token"])


def _advance_to_loading(
    client: TestClient,
    admin_headers: dict[str, str],
    driver_headers: dict[str, str],
    order_id: str,
    driver_id: str,
) -> None:
    assign = client.post(
        f"/api/v1/orders/{order_id}/assign-driver",
        headers=admin_headers,
        json={"driver_id": driver_id},
    )
    assert assign.status_code == 200, assign.text
    for step in ("accept", "arrive-pickup", "start-loading"):
        response = client.post(
            f"/api/v1/orders/{order_id}/{step}",
            headers=driver_headers,
        )
        assert response.status_code == 200, f"{step}: {response.text}"


def _verify_order_vehicles(
    client: TestClient,
    headers: dict[str, str],
    order_id: str,
) -> None:
    vehicles = client.get(f"/api/v1/orders/{order_id}", headers=headers)
    for vehicle in vehicles.json()["data"]["vehicles"]:
        client.post(
            f"/api/v1/orders/{order_id}/vehicles/{vehicle['id']}/verify-vin",
            headers=headers,
            json={"vin": vehicle["vin"] or "LSJWP4396TZ174225"},
        )


def test_order_stores_customer_reference_numbers(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Orders persist structured customer reference numbers."""
    headers = _auth(admin_tokens["access_token"])
    order_id = _create_order_with_references(client, headers)
    fetched = client.get(f"/api/v1/orders/{order_id}", headers=headers)
    assert fetched.status_code == 200
    assert fetched.json()["data"]["customer_reference_numbers"] == [
        "31MGBE4985",
        "31MGBE5029",
    ]


def test_cmr_preview_returns_pdf_at_loading(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Driver can preview a generated CMR PDF during loading."""
    admin_headers = _auth(admin_tokens["access_token"])
    driver_id, driver_headers = _create_driver(
        client, admin_headers, "cmr.preview@example.com"
    )
    order_id = _create_order_with_references(client, admin_headers)
    _advance_to_loading(client, admin_headers, driver_headers, order_id, driver_id)

    preview = client.get(f"/api/v1/orders/{order_id}/cmr/preview", headers=driver_headers)
    assert preview.status_code == 200, preview.text
    assert preview.headers["content-type"] == "application/pdf"
    assert preview.content[:4] == b"%PDF"
    reader = PdfReader(io.BytesIO(preview.content))
    text = "".join(page.extract_text() or "" for page in reader.pages)
    assert "31MGBE4985" in text
    assert "31MGBE5029" in text
    assert "LSJWP4396TZ174225" in text
    assert "1. LSJWP4396TZ174225" in text
    assert "MG" in text
    assert "Expéditeur" in text or "Afzender" in text
    assert "Transporteur" in text or "Vervoerder" in text
    assert "Pickup Co" in text
    assert "Delivery Co" in text
    assert "Sign and stamp by hand" not in text
    assert "Handtekening en stempel van de vervoerder" in text


def test_generate_cmr_required_before_finish_loading(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Finish loading is blocked until a CMR draft is generated."""
    admin_headers = _auth(admin_tokens["access_token"])
    driver_id, driver_headers = _create_driver(
        client, admin_headers, "cmr.loading@example.com"
    )
    order_id = _create_order_with_references(client, admin_headers)
    _advance_to_loading(client, admin_headers, driver_headers, order_id, driver_id)
    _verify_order_vehicles(client, driver_headers, order_id)

    blocked = client.post(
        f"/api/v1/orders/{order_id}/complete-loading",
        headers=driver_headers,
    )
    assert blocked.status_code == 422
    assert blocked.json()["error"]["code"] == "CMR_REQUIRED"

    generate = client.post(
        f"/api/v1/orders/{order_id}/cmr/generate",
        headers=driver_headers,
    )
    assert generate.status_code == 200, generate.text
    payload = generate.json()["data"]
    assert payload["document_type"] == "CMR"
    assert payload["is_locked"] is False

    finished = client.post(
        f"/api/v1/orders/{order_id}/complete-loading",
        headers=driver_headers,
    )
    assert finished.status_code == 200, finished.text
    assert finished.json()["data"]["status"] == "LOADED"

    checklist = client.get(
        f"/api/v1/orders/{order_id}/completion-checklist",
        headers=driver_headers,
    )
    assert checklist.json()["data"]["documents_uploaded"] is False


def test_delivery_requires_signed_cmr_upload_before_completion(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Delivery requires signed CMR upload, finish delivery, then job completion."""
    admin_headers = _auth(admin_tokens["access_token"])
    driver_id, driver_headers = _create_driver(
        client, admin_headers, "cmr.delivery@example.com"
    )
    order_id = _create_order_with_references(client, admin_headers)
    _advance_to_loading(client, admin_headers, driver_headers, order_id, driver_id)
    _verify_order_vehicles(client, driver_headers, order_id)
    client.post(f"/api/v1/orders/{order_id}/cmr/generate", headers=driver_headers)

    for step in ("complete-loading", "start-transit", "arrive-delivery"):
        response = client.post(
            f"/api/v1/orders/{order_id}/{step}",
            headers=driver_headers,
        )
        assert response.status_code == 200, step

    blocked_finish = client.post(
        f"/api/v1/orders/{order_id}/finish-delivery",
        headers=driver_headers,
    )
    assert blocked_finish.status_code == 422
    assert blocked_finish.json()["error"]["code"] == "CMR_REQUIRED"

    blocked_complete = client.post(
        f"/api/v1/orders/{order_id}/complete-delivery",
        headers=driver_headers,
    )
    assert blocked_complete.status_code == 422

    _upload_signed_cmr(client, driver_headers, order_id)

    order = client.get(f"/api/v1/orders/{order_id}", headers=driver_headers)
    assert order.json()["data"]["status"] == "ARRIVED_DELIVERY"

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

    documents = client.get(
        f"/api/v1/orders/{order_id}/documents",
        headers=admin_headers,
    )
    assert documents.status_code == 200
    cmr_versions = [
        doc["version"]
        for doc in documents.json()["data"]
        if doc["document_type"] == "CMR"
    ]
    assert max(cmr_versions) >= 2


def test_cmr_preview_lists_stock_id_vin_model_and_plate(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Generated CMR shows per-vehicle Stock ID, VIN, model and license plate."""
    admin_headers = _auth(admin_tokens["access_token"])
    driver_id, driver_headers = _create_driver(
        client, admin_headers, "cmr.stock@example.com"
    )
    customer_id = _create_customer(client, admin_headers)
    response = client.post(
        "/api/v1/orders",
        headers=admin_headers,
        json={
            "customer_id": customer_id,
            "customer_reference_numbers": ["LL-ORDER-REF"],
            "planned_pickup_date": "2026-08-12",
            "planned_delivery_date": "2026-08-14",
            "stops": [
                {
                    "stop_type": "PICKUP",
                    "sequence": 1,
                    "company_name": "Pickup Co",
                    "city": "Antwerp",
                    "country": "BE",
                },
                {
                    "stop_type": "DELIVERY",
                    "sequence": 2,
                    "company_name": "Delivery Co",
                    "city": "Brussels",
                    "country": "BE",
                },
            ],
            "vehicles": [
                {
                    "make": "Renault",
                    "model": "Trafic 1.9 Diesel",
                    "vin": "VF1FLACA66Y130037",
                    "notes": "Stock ID: HN60935\nLicense plate: 1WST863",
                }
            ],
        },
    )
    assert response.status_code == 201, response.text
    order_id = response.json()["data"]["id"]
    _advance_to_loading(client, admin_headers, driver_headers, order_id, driver_id)

    preview = client.get(f"/api/v1/orders/{order_id}/cmr/preview", headers=driver_headers)
    assert preview.status_code == 200, preview.text
    reader = PdfReader(io.BytesIO(preview.content))
    text = "".join(page.extract_text() or "" for page in reader.pages)

    assert "HN60935" in text
    assert "1WST863" in text
    assert "VF1FLACA66Y130037" in text
    assert "Renault" in text
    assert "Trafic 1.9 Diesel" in text
    assert "LL-ORDER-REF" in text
    assert text.count("HN60935") == 1
