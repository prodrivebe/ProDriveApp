"""Document and photo endpoint tests."""

import io

from fastapi.testclient import TestClient

MINIMAL_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
    b"\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
    b"\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01"
    b"\x0d\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
)


def _create_customer(client: TestClient, headers: dict[str, str]) -> str:
    response = client.post(
        "/api/v1/customers",
        headers=headers,
        json={"company_name": "Document Customer GmbH"},
    )
    assert response.status_code == 201
    return response.json()["data"]["id"]


def _create_order_with_vehicle(client: TestClient, headers: dict[str, str]) -> tuple[str, str]:
    customer_id = _create_customer(client, headers)
    response = client.post(
        "/api/v1/orders",
        headers=headers,
        json={
            "customer_id": customer_id,
            "vehicles": [{"make": "BMW", "model": "X5"}],
        },
    )
    assert response.status_code == 201
    order_id = response.json()["data"]["id"]
    vehicle_id = response.json()["data"]["vehicles"][0]["id"]
    return order_id, vehicle_id


def test_admin_can_generate_and_download_cmr(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Admin can generate and fetch a CMR document."""
    headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
    order_id, _ = _create_order_with_vehicle(client, headers)

    generate_response = client.post(
        f"/api/v1/orders/{order_id}/cmr/generate",
        headers=headers,
    )
    assert generate_response.status_code == 200
    assert generate_response.json()["data"]["document_type"] == "CMR"

    get_response = client.get(f"/api/v1/orders/{order_id}/cmr", headers=headers)
    assert get_response.status_code == 200
    assert get_response.json()["data"]["file_path"].startswith("/uploads/")


def test_admin_can_upload_vehicle_photo(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Admin can upload and list vehicle photos."""
    headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
    _, vehicle_id = _create_order_with_vehicle(client, headers)

    upload_response = client.post(
        f"/api/v1/vehicles/{vehicle_id}/photos",
        headers=headers,
        files={"file": ("front.png", io.BytesIO(MINIMAL_PNG), "image/png")},
        data={"photo_type": "FRONT"},
    )
    assert upload_response.status_code == 201
    assert upload_response.json()["data"]["photo_type"] == "FRONT"

    list_response = client.get(
        f"/api/v1/vehicles/{vehicle_id}/photos",
        headers=headers,
    )
    assert list_response.status_code == 200
    assert len(list_response.json()["data"]) == 1


def test_assigned_driver_can_generate_cmr_after_loading(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Assigned driver can generate CMR for their active order after loading."""
    from tests.test_driver_app import _create_driver_with_login

    admin_headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
    driver_id, driver_headers = _create_driver_with_login(client, admin_headers)
    customer_id = _create_customer(client, admin_headers)
    order_response = client.post(
        "/api/v1/orders",
        headers=admin_headers,
        json={"customer_id": customer_id, "vehicles": [{"make": "Audi", "model": "A4"}]},
    )
    order_id = order_response.json()["data"]["id"]
    client.post(
        f"/api/v1/orders/{order_id}/assign-driver",
        headers=admin_headers,
        json={"driver_id": driver_id},
    )

    for path in ("accept", "arrive-pickup", "complete-loading"):
        response = client.post(
            f"/api/v1/orders/{order_id}/{path}",
            headers=driver_headers,
        )
        assert response.status_code == 200, response.text

    generate_response = client.post(
        f"/api/v1/orders/{order_id}/cmr/generate",
        headers=driver_headers,
    )
    assert generate_response.status_code == 200
    assert generate_response.json()["data"]["document_type"] == "CMR"


def test_driver_cannot_generate_cmr_for_other_drivers_order(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Driver cannot generate CMR for another driver's assigned order."""
    from tests.test_driver_app import _create_driver_with_login

    admin_headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
    driver_one_id, driver_one_headers = _create_driver_with_login(client, admin_headers)
    _, driver_two_headers = _create_driver_with_login(
        client,
        admin_headers,
        email="other.driver@example.com",
    )
    customer_id = _create_customer(client, admin_headers)
    order_response = client.post(
        "/api/v1/orders",
        headers=admin_headers,
        json={"customer_id": customer_id, "vehicles": [{"make": "Volvo", "model": "XC60"}]},
    )
    order_id = order_response.json()["data"]["id"]
    client.post(
        f"/api/v1/orders/{order_id}/assign-driver",
        headers=admin_headers,
        json={"driver_id": driver_one_id},
    )

    for path in ("accept", "arrive-pickup", "complete-loading"):
        client.post(f"/api/v1/orders/{order_id}/{path}", headers=driver_one_headers)

    denied = client.post(
        f"/api/v1/orders/{order_id}/cmr/generate",
        headers=driver_two_headers,
    )
    assert denied.status_code == 403
    assert denied.json()["error"]["code"] == "FORBIDDEN"


def test_admin_can_upload_signed_cmr(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Admin can upload a signed CMR copy."""
    headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
    order_id, _ = _create_order_with_vehicle(client, headers)
    client.post(f"/api/v1/orders/{order_id}/cmr/generate", headers=headers)

    upload_response = client.post(
        f"/api/v1/orders/{order_id}/cmr/upload",
        headers=headers,
        files={"file": ("signed-cmr.png", io.BytesIO(MINIMAL_PNG), "image/png")},
    )
    assert upload_response.status_code == 201
    assert upload_response.json()["data"]["document_type"] == "CMR_SIGNED"
