"""Health endpoint tests."""

from fastapi.testclient import TestClient


def test_health_endpoint_returns_expected_payload(client: TestClient) -> None:
    """Health endpoint returns service status."""
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": "ProDrive API",
        "version": "0.1.0",
    }


def test_openapi_documentation_is_available(client: TestClient) -> None:
    """OpenAPI schema is exposed for API documentation."""
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert response.json()["info"]["title"] == "ProDrive API"
