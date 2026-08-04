"""Company endpoint tests."""

import io

from fastapi.testclient import TestClient


def test_get_my_company_as_admin(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Admin can read company profile."""
    headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
    response = client.get("/api/v1/companies/me", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["name"] == "Test Transport"


def test_update_company_requires_admin(client: TestClient) -> None:
    """Dispatcher cannot update company profile."""
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "dispatcher@example.com",
            "password": "Dispatch123!",
        },
    )
    access_token = login_response.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.put(
        "/api/v1/companies/me",
        headers=headers,
        json={
            "name": "Updated Transport",
            "vat_number": "VAT123",
            "address": "Main Street 1",
            "country": "NL",
            "phone": "+31123456789",
            "email": "company@example.com",
            "subscription_plan": "standard",
        },
    )

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_update_company_as_admin(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Admin can update company profile."""
    headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
    response = client.put(
        "/api/v1/companies/me",
        headers=headers,
        json={
            "name": "Updated Transport",
            "vat_number": "VAT123",
            "address": "Main Street 1",
            "country": "NL",
            "phone": "+31123456789",
            "email": "company@example.com",
            "subscription_plan": "standard",
        },
    )

    assert response.status_code == 200
    assert response.json()["data"]["name"] == "Updated Transport"


def test_get_company_settings_as_dispatcher(client: TestClient) -> None:
    """Dispatcher can read company settings."""
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "dispatcher@example.com",
            "password": "Dispatch123!",
        },
    )
    access_token = login_response.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get("/api/v1/companies/settings", headers=headers)

    assert response.status_code == 200
    assert response.json()["data"]["default_currency"] == "EUR"


def test_update_company_settings_as_admin(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Admin can update settings and branding."""
    headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
    response = client.put(
        "/api/v1/companies/settings",
        headers=headers,
        json={
            "timezone": "Europe/Amsterdam",
            "default_currency": "EUR",
            "order_number_prefix": "PD",
            "require_vehicle_photos": True,
            "primary_color": "#112233",
            "secondary_color": "#AABBCC",
            "accent_color": "#FF9900",
            "dashboard_title": "ProDrive Dispatch",
        },
    )

    assert response.status_code == 200
    body = response.json()["data"]
    assert body["timezone"] == "Europe/Amsterdam"
    assert body["primary_color"] == "#112233"
    assert body["dashboard_title"] == "ProDrive Dispatch"


def test_upload_company_logo(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Admin can upload a company logo."""
    png_bytes = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
        b"\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
        b"\x00\x00\x00\x0bIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01"
        b"\x0d\n\x2d\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
    response = client.post(
        "/api/v1/companies/me/logo",
        headers=headers,
        files={"logo": ("logo.png", io.BytesIO(png_bytes), "image/png")},
    )

    assert response.status_code == 200
    logo_url = response.json()["data"]["logo_url"]
    assert logo_url.startswith("/uploads/companies/")


def test_company_endpoints_require_authentication(client: TestClient) -> None:
    """Company endpoints reject unauthenticated requests."""
    response = client.get("/api/v1/companies/me")
    assert response.status_code == 401
