"""Authentication endpoint tests."""

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.audit.models import AuditLog
from app.config.settings import Settings


def test_login_success(
    client: TestClient,
    test_settings: Settings,
) -> None:
    """Valid credentials return token pair."""
    response = client.post(
        "/api/v1/auth/login",
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
    assert body["data"]["expires_in"] == 900


def test_login_invalid_password(client: TestClient, test_settings: Settings) -> None:
    """Invalid password returns authentication error."""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": test_settings.seed_admin_email,
            "password": "WrongPassword123!",
        },
    )

    assert response.status_code == 401
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "INVALID_CREDENTIALS"


def test_refresh_token(client: TestClient, admin_tokens: dict[str, str]) -> None:
    """Refresh token returns a rotated token pair."""
    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": admin_tokens["refresh_token"]},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["access_token"]
    assert body["data"]["refresh_token"]


def test_logout(client: TestClient, admin_tokens: dict[str, str]) -> None:
    """Logout revokes refresh token."""
    headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
    response = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": admin_tokens["refresh_token"]},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["data"]["message"] == "Logged out successfully."

    refresh_response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": admin_tokens["refresh_token"]},
    )
    assert refresh_response.status_code == 401


def test_me_endpoint(client: TestClient, admin_tokens: dict[str, str]) -> None:
    """Authenticated user can fetch profile."""
    headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
    response = client.get("/api/v1/auth/me", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["email"] == "admin@example.com"
    assert body["data"]["role"] == "ADMIN"


def test_me_requires_authentication(client: TestClient) -> None:
    """Profile endpoint rejects unauthenticated requests."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_role_authorization_allows_admin(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Admin-only endpoint allows admin users."""
    headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
    response = client.get("/api/v1/auth/admin-check", headers=headers)
    assert response.status_code == 200
    assert response.json()["data"]["role"] == "ADMIN"


def test_role_authorization_blocks_dispatcher(client: TestClient) -> None:
    """Admin-only endpoint rejects dispatcher users."""
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "dispatcher@example.com",
            "password": "Dispatch123!",
        },
    )
    access_token = login_response.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get("/api/v1/auth/admin-check", headers=headers)
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "FORBIDDEN"


def test_password_reset_flow(client: TestClient, test_settings: Settings) -> None:
    """Password reset request and confirmation update credentials."""
    request_response = client.post(
        "/api/v1/auth/password-reset/request",
        json={"email": test_settings.seed_admin_email},
    )
    assert request_response.status_code == 200
    reset_token = request_response.json()["meta"]["reset_token"]

    confirm_response = client.post(
        "/api/v1/auth/password-reset/confirm",
        json={
            "token": reset_token,
            "new_password": "NewAdmin123!",
        },
    )
    assert confirm_response.status_code == 200

    old_login = client.post(
        "/api/v1/auth/login",
        json={
            "email": test_settings.seed_admin_email,
            "password": test_settings.seed_admin_password,
        },
    )
    assert old_login.status_code == 401

    new_login = client.post(
        "/api/v1/auth/login",
        json={
            "email": test_settings.seed_admin_email,
            "password": "NewAdmin123!",
        },
    )
    assert new_login.status_code == 200


def test_login_creates_audit_log(
    client: TestClient,
    test_settings: Settings,
    db_session: Session,
) -> None:
    """Successful login creates an audit log entry."""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": test_settings.seed_admin_email,
            "password": test_settings.seed_admin_password,
        },
    )
    assert response.status_code == 200

    logs = list(db_session.scalars(select(AuditLog)).all())
    assert any(log.action == "LOGIN_SUCCESS" for log in logs)
