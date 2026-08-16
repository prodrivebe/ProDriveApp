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
    monkeypatch,
) -> None:
    """OPTIONS /auth/login from prodriveservice.eu succeeds as a CORS preflight."""
    monkeypatch.setenv("APP_ENV", "production")
    from app.config.settings import get_settings

    get_settings.cache_clear()
    from app.main import create_app

    prod_client = TestClient(create_app())
    response = prod_client.options(
        "/api/v1/auth/login",
        headers=_preflight_headers("https://prodriveservice.eu"),
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "https://prodriveservice.eu"
    assert "POST" in response.headers["access-control-allow-methods"]
    assert response.headers["access-control-allow-credentials"] == "true"


def test_login_preflight_rejects_unapproved_origin(
    client: TestClient,
    monkeypatch,
) -> None:
    """OPTIONS /auth/login from an unapproved origin is rejected."""
    monkeypatch.setenv("APP_ENV", "production")
    from app.config.settings import get_settings

    get_settings.cache_clear()
    from app.main import create_app

    prod_client = TestClient(create_app())
    response = prod_client.options(
        "/api/v1/auth/login",
        headers=_preflight_headers("https://evil.example.com"),
    )

    assert response.status_code == 400
