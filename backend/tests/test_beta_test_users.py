"""Beta field-test user login and RBAC checks."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.companies.models import Company
from app.scripts.demo_data import ensure_demo_lookup_data
from app.scripts.ensure_beta_test_users import (
    BETA_DISPATCHER_EMAIL,
    BETA_DISPATCHER_PASSWORD,
    BETA_DRIVER_EMAIL,
    BETA_DRIVER_PASSWORD,
    ensure_beta_test_users,
)


def _login(client: TestClient, email: str, password: str) -> dict[str, str]:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    return {
        "access_token": data["access_token"],
        "refresh_token": data["refresh_token"],
    }


def test_beta_driver_login_and_driver_endpoints(
    client: TestClient,
    db_session: Session,
) -> None:
    """Field driver account authenticates and can access driver-only routes."""
    company = db_session.query(Company).first()
    assert company is not None

    ensure_demo_lookup_data(db_session, company.id)
    summary = ensure_beta_test_users(company_id=company.id, db=db_session)
    assert summary["driver"]["email"] == BETA_DRIVER_EMAIL

    tokens = _login(client, BETA_DRIVER_EMAIL, BETA_DRIVER_PASSWORD)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    profile = client.get("/api/v1/auth/me", headers=headers)
    assert profile.status_code == 200
    assert profile.json()["data"]["role"] == "DRIVER"
    assert profile.json()["data"]["email"] == BETA_DRIVER_EMAIL

    home = client.get("/api/v1/drivers/me/home", headers=headers)
    assert home.status_code == 200, home.text

    admin_check = client.get("/api/v1/auth/admin-check", headers=headers)
    assert admin_check.status_code == 403
    assert admin_check.json()["error"]["code"] == "FORBIDDEN"


def test_beta_dispatcher_login_and_dispatcher_endpoints(
    client: TestClient,
    db_session: Session,
) -> None:
    """Field dispatcher account authenticates and can access fleet routes."""
    company = db_session.query(Company).first()
    assert company is not None

    ensure_demo_lookup_data(db_session, company.id)
    summary = ensure_beta_test_users(company_id=company.id, db=db_session)
    assert summary["dispatcher"]["email"] == BETA_DISPATCHER_EMAIL

    tokens = _login(client, BETA_DISPATCHER_EMAIL, BETA_DISPATCHER_PASSWORD)
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    profile = client.get("/api/v1/auth/me", headers=headers)
    assert profile.status_code == 200
    assert profile.json()["data"]["role"] == "DISPATCHER"

    drivers = client.get("/api/v1/drivers", headers=headers, params={"page_size": 10})
    assert drivers.status_code == 200

    driver_home = client.get("/api/v1/drivers/me/home", headers=headers)
    assert driver_home.status_code == 403
    assert driver_home.json()["error"]["code"] == "FORBIDDEN"


def test_beta_test_users_seed_is_idempotent(
    client: TestClient,
    db_session: Session,
) -> None:
    """Running the beta user seed twice keeps stable user ids."""
    company = db_session.query(Company).first()
    assert company is not None

    ensure_demo_lookup_data(db_session, company.id)
    first = ensure_beta_test_users(company_id=company.id, db=db_session)
    second = ensure_beta_test_users(company_id=company.id, db=db_session)

    assert first["driver"]["user_id"] == second["driver"]["user_id"]
    assert first["dispatcher"]["user_id"] == second["dispatcher"]["user_id"]
