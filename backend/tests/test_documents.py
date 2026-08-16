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


def test_admin_can_list_order_documents(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Admin can list order documents for dispatcher order detail."""
    headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
    order_id, _ = _create_order_with_vehicle(client, headers)

    empty_response = client.get(
        f"/api/v1/orders/{order_id}/documents",
        headers=headers,
    )
    assert empty_response.status_code == 200
    assert empty_response.json()["data"] == []

    client.post(f"/api/v1/orders/{order_id}/cmr/generate", headers=headers)
    documents_response = client.get(
        f"/api/v1/orders/{order_id}/documents",
        headers=headers,
    )
    assert documents_response.status_code == 200
    documents = documents_response.json()["data"]
    assert len(documents) == 1
    assert documents[0]["document_type"] == "CMR"
    assert documents[0]["version"] == 2


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
