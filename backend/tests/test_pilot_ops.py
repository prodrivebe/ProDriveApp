"""Pilot deployment infrastructure tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.config.settings import Settings
from app.main import create_app


def _build_client(**settings_overrides: object) -> TestClient:
    settings = Settings(
        environment="test",
        jwt_secret_key="test-secret-key-with-32-byte-minimum-length",
        **settings_overrides,
    )
    return TestClient(create_app(settings))


def test_ops_status_reports_feature_flags() -> None:
    client = _build_client(
        feature_ai_enabled=False,
        feature_planning_enabled=True,
        maintenance_mode=False,
    )
    response = client.get("/api/v1/health/ops")
    assert response.status_code == 200
    payload = response.json()
    assert payload["maintenance_mode"] is False
    assert payload["feature_flags"]["ai"] is False
    assert payload["feature_flags"]["planning"] is True


def test_maintenance_mode_blocks_api_but_not_health() -> None:
    client = _build_client(maintenance_mode=True)
    health = client.get("/api/v1/health")
    assert health.status_code == 200

    blocked = client.get("/api/v1/orders")
    assert blocked.status_code == 503
    assert blocked.json()["error"]["code"] == "MAINTENANCE_MODE"


def test_feature_flag_blocks_ai_routes() -> None:
    client = _build_client(feature_ai_enabled=False)
    response = client.get("/api/v1/ai/suggestions")
    assert response.status_code in {401, 403, 503}
    if response.status_code == 503:
        assert response.json()["error"]["code"] == "FEATURE_DISABLED"


def test_auth_rate_limit_returns_429() -> None:
    client = _build_client(auth_rate_limit_per_minute=2)
    payload = {"email": "missing@example.com", "password": "wrong-password"}
    first = client.post("/api/v1/auth/login", json=payload)
    second = client.post("/api/v1/auth/login", json=payload)
    third = client.post("/api/v1/auth/login", json=payload)
    assert first.status_code in {401, 422}
    assert second.status_code in {401, 422}
    assert third.status_code == 429
    assert third.json()["error"]["code"] == "RATE_LIMIT_EXCEEDED"
