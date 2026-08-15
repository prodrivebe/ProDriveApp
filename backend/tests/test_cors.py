"""CORS preflight tests."""

from fastapi.testclient import TestClient


def _preflight_headers(origin: str) -> dict[str, str]:
    return {
        "Origin": origin,
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "authorization,content-type",
    }


def test_login_preflight_allows_production_dispatcher_origin(
    client: TestClient,
) -> None:
    """OPTIONS /auth/login from prodriveservice.eu succeeds as a CORS preflight."""
    response = client.options(
        "/api/v1/auth/login",
        headers=_preflight_headers("https://prodriveservice.eu"),
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://prodriveservice.eu"
    assert "POST" in response.headers["access-control-allow-methods"]
    assert response.headers["access-control-allow-credentials"] == "true"


def test_login_preflight_rejects_unapproved_origin(client: TestClient) -> None:
    """OPTIONS /auth/login from an unapproved origin is rejected."""
    response = client.options(
        "/api/v1/auth/login",
        headers=_preflight_headers("https://evil.example.com"),
    )

    assert response.status_code == 400
