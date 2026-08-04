"""User endpoint tests."""

from fastapi.testclient import TestClient


def test_admin_can_list_users(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Admin can list company users."""
    headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
    response = client.get("/api/v1/users", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert len(body["data"]) >= 2
    assert body["meta"]["pagination"]["total"] >= 2


def test_dispatcher_cannot_list_users(client: TestClient) -> None:
    """Dispatcher cannot list users."""
    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "dispatcher@example.com",
            "password": "Dispatch123!",
        },
    )
    access_token = login_response.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {access_token}"}
    response = client.get("/api/v1/users", headers=headers)

    assert response.status_code == 403


def test_admin_can_create_driver(client: TestClient, admin_tokens: dict[str, str]) -> None:
    """Admin can create a driver user."""
    headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
    response = client.post(
        "/api/v1/users",
        headers=headers,
        json={
            "first_name": "John",
            "last_name": "Driver",
            "email": "driver@example.com",
            "password": "Driver123!",
            "role": "DRIVER",
            "is_active": True,
        },
    )

    assert response.status_code == 201
    assert response.json()["data"]["role"] == "DRIVER"


def test_user_can_update_own_profile(client: TestClient) -> None:
    """Authenticated user can update own profile."""
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
        "/api/v1/users/me",
        headers=headers,
        json={
            "first_name": "Updated",
            "last_name": "Dispatcher",
            "email": "dispatcher@example.com",
        },
    )

    assert response.status_code == 200
    assert response.json()["data"]["first_name"] == "Updated"


def test_user_can_change_own_password(client: TestClient) -> None:
    """Authenticated user can change own password."""
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
        "/api/v1/users/me/password",
        headers=headers,
        json={
            "current_password": "Dispatch123!",
            "new_password": "Dispatch456!",
        },
    )

    assert response.status_code == 200

    relogin = client.post(
        "/api/v1/auth/login",
        json={
            "email": "dispatcher@example.com",
            "password": "Dispatch456!",
        },
    )
    assert relogin.status_code == 200


def test_admin_can_soft_delete_user(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Admin can soft delete another user."""
    headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
    create_response = client.post(
        "/api/v1/users",
        headers=headers,
        json={
            "first_name": "Temp",
            "last_name": "Driver",
            "email": "tempdriver@example.com",
            "password": "Driver123!",
            "role": "DRIVER",
            "is_active": True,
        },
    )
    user_id = create_response.json()["data"]["id"]

    delete_response = client.delete(
        f"/api/v1/users/{user_id}",
        headers=headers,
    )
    assert delete_response.status_code == 200

    get_response = client.get(
        f"/api/v1/users/{user_id}",
        headers=headers,
    )
    assert get_response.status_code == 404


def test_admin_cannot_delete_self(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    """Admin cannot delete their own account."""
    headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
    profile = client.get("/api/v1/users/me", headers=headers)
    user_id = profile.json()["data"]["id"]

    response = client.delete(f"/api/v1/users/{user_id}", headers=headers)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_OPERATION"
