"""Security-focused beta readiness tests."""

from __future__ import annotations

from fastapi.testclient import TestClient


PROTECTED_ENDPOINTS = [
    ("GET", "/api/v1/orders"),
    ("GET", "/api/v1/customers"),
    ("GET", "/api/v1/planning/board"),
    ("GET", "/api/v1/ai/suggestions"),
    ("GET", "/api/v1/notifications"),
]


def test_protected_endpoints_require_authentication(client: TestClient) -> None:
    """Unauthenticated requests to business endpoints are rejected."""
    for method, path in PROTECTED_ENDPOINTS:
        response = client.request(method, path)
        assert response.status_code == 401, f"{method} {path} should require auth"


def test_error_responses_use_standard_envelope(client: TestClient) -> None:
    """Unauthorized responses follow the standard error envelope."""
    response = client.get("/api/v1/orders")
    assert response.status_code == 401
    payload = response.json()
    assert payload["success"] is False
    assert "error" in payload
    assert "code" in payload["error"]
    assert "message" in payload["error"]


def test_validation_errors_use_standard_code(client: TestClient, admin_tokens: dict[str, str]) -> None:
    """Validation failures return VALIDATION_ERROR code."""
    headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
    response = client.post("/api/v1/ai/parse-order", headers=headers, json={"message": ""})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
