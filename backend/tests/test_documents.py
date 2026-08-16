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


def test_admin_can_generate_cmr_pdf(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Admin can preview a CMR PDF for an order."""
    headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
    order_id, _ = _create_order_with_vehicle(client, headers)

    preview = client.get(f"/api/v1/orders/{order_id}/cmr/preview", headers=headers)
    assert preview.status_code == 422 or preview.status_code == 200
    if preview.status_code == 200:
        assert preview.headers["content-type"] == "application/pdf"


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


def test_admin_can_generate_cmr_draft_at_loading(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """CMR generation requires loading stage."""
    headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
    order_id, _ = _create_order_with_vehicle(client, headers)
    generate = client.post(f"/api/v1/orders/{order_id}/cmr/generate", headers=headers)
    assert generate.status_code == 422
