"""Mobile demo driver login and home screen data."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.companies.models import Company
from app.scripts.demo_data import ensure_demo_lookup_data
from app.scripts.ensure_mobile_demo_driver import (
    DEMO_MOBILE_DRIVER_EMAIL,
    DEMO_MOBILE_DRIVER_PASSWORD,
    ensure_mobile_demo_driver,
)


def test_mobile_demo_driver_login_and_home(
    client: TestClient,
    db_session: Session,
) -> None:
    """Canonical driver app account can authenticate and sees an active order."""
    company = db_session.query(Company).first()
    assert company is not None

    ensure_demo_lookup_data(db_session, company.id)
    summary = ensure_mobile_demo_driver(company_id=company.id)
    assert summary["active_orders"] >= 1

    login = client.post(
        "/api/v1/auth/login",
        json={
            "email": DEMO_MOBILE_DRIVER_EMAIL,
            "password": DEMO_MOBILE_DRIVER_PASSWORD,
        },
    )
    assert login.status_code == 200, login.text
    body = login.json()
    assert body["success"] is True
    assert body["data"]["access_token"]
    assert body["data"]["refresh_token"]

    headers = {"Authorization": f"Bearer {body['data']['access_token']}"}
    home = client.get("/api/v1/drivers/me/home", headers=headers)
    assert home.status_code == 200, home.text
    home_data = home.json()["data"]
    assert home_data["current_order"] is not None
    assert home_data["current_order"]["order_number"]

    orders = client.get("/api/v1/drivers/me/orders", headers=headers)
    assert orders.status_code == 200
    assert len(orders.json()["data"]) >= 1
