"""Verify shared API route manifest matches the FastAPI application."""

from app.common.api_routes import (
    api_v1_prefix,
    full_api_path,
    iter_manifest_paths,
    load_api_routes_manifest,
)
from app.config.settings import Settings
from fastapi.testclient import TestClient


def test_shared_manifest_uses_api_v1_prefix() -> None:
    manifest = load_api_routes_manifest()
    assert manifest["apiV1Prefix"] == "/api/v1"
    assert api_v1_prefix() == "/api/v1"


def test_shared_auth_routes_exist_on_fastapi_app(client: TestClient) -> None:
    openapi_paths = set(client.app.openapi()["paths"].keys())

    for key, path in iter_manifest_paths():
        assert path in openapi_paths, f"Missing FastAPI route for manifest entry {key}: {path}"


def test_login_endpoint_integration(client: TestClient, test_settings: Settings) -> None:
    """Login must be reachable at the shared manifest path, not the legacy /api/auth path."""
    login_path = full_api_path("auth", "login")
    assert login_path == "/api/v1/auth/login"

    legacy_response = client.post(
        "/api/auth/login",
        json={
            "email": test_settings.seed_admin_email,
            "password": test_settings.seed_admin_password,
        },
    )
    assert legacy_response.status_code == 404

    response = client.post(
        login_path,
        json={
            "email": test_settings.seed_admin_email,
            "password": test_settings.seed_admin_password,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["token_type"] == "bearer"
    assert body["data"]["access_token"]
    assert body["data"]["refresh_token"]
