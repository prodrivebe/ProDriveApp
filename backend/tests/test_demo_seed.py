"""Demo lookup seed tests."""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.scripts.demo_data import (
    DEMO_CUSTOMER_COUNT,
    DEMO_DRIVER_COUNT,
    DEMO_TRAILER_COUNT,
    DEMO_TRUCK_COUNT,
    count_demo_entities,
    ensure_demo_lookup_data,
)
from app.customers.models import Customer


def test_demo_lookup_seed_populates_order_form_data(
    client: TestClient,
    db_session: Session,
    dispatcher_tokens: dict[str, str],
) -> None:
    """Demo seed creates the full QA dataset usable by dispatchers."""
    from app.companies.models import Company

    company = db_session.query(Company).first()
    assert company is not None

    ensure_demo_lookup_data(db_session, company.id)

    dispatcher_headers = {"Authorization": f"Bearer {dispatcher_tokens['access_token']}"}
    customers = client.get("/api/v1/customers", headers=dispatcher_headers, params={"page_size": 100})
    drivers = client.get("/api/v1/drivers", headers=dispatcher_headers, params={"page_size": 100})
    trucks = client.get("/api/v1/trucks", headers=dispatcher_headers, params={"page_size": 100})
    trailers = client.get("/api/v1/trailers", headers=dispatcher_headers, params={"page_size": 100})

    assert customers.status_code == 200
    assert drivers.status_code == 200
    assert trucks.status_code == 200
    assert trailers.status_code == 200
    assert len(customers.json()["data"]) >= DEMO_CUSTOMER_COUNT
    assert len(drivers.json()["data"]) >= DEMO_DRIVER_COUNT
    assert drivers.json()["data"][0]["first_name"]
    assert len(trucks.json()["data"]) >= DEMO_TRUCK_COUNT
    assert trucks.json()["data"][0]["brand"]
    assert len(trailers.json()["data"]) >= DEMO_TRAILER_COUNT


def test_demo_seed_is_idempotent(client: TestClient, db_session: Session) -> None:
    """Running the demo seed twice yields the same canonical dataset counts."""
    from app.companies.models import Company

    company = db_session.query(Company).first()
    assert company is not None

    ensure_demo_lookup_data(db_session, company.id)
    first = count_demo_entities(db_session, company.id)

    db_session.add(
        Customer(
            company_id=company.id,
            company_name="Extra QA Customer",
            city="Brussels",
            country="BE",
        )
    )
    db_session.commit()

    ensure_demo_lookup_data(db_session, company.id)
    second = count_demo_entities(db_session, company.id)

    assert first == second
    assert second == {
        "customers": DEMO_CUSTOMER_COUNT,
        "drivers": DEMO_DRIVER_COUNT,
        "trucks": DEMO_TRUCK_COUNT,
        "trailers": DEMO_TRAILER_COUNT,
        "orders": 8,
    }


def test_dispatcher_can_create_and_assign_full_order(
    client: TestClient,
    db_session: Session,
    dispatcher_tokens: dict[str, str],
) -> None:
    """Full order wizard flow works for dispatchers using demo lookup data."""
    from app.companies.models import Company

    company = db_session.query(Company).first()
    assert company is not None
    ensure_demo_lookup_data(db_session, company.id)

    headers = {"Authorization": f"Bearer {dispatcher_tokens['access_token']}"}
    customers = client.get("/api/v1/customers", headers=headers, params={"page_size": 100}).json()["data"]
    drivers = client.get("/api/v1/drivers", headers=headers, params={"page_size": 100}).json()["data"]
    trucks = client.get("/api/v1/trucks", headers=headers, params={"page_size": 100}).json()["data"]
    trailers = client.get("/api/v1/trailers", headers=headers, params={"page_size": 100}).json()["data"]

    create_response = client.post(
        "/api/v1/orders",
        headers=headers,
        json={
            "customer_id": customers[0]["id"],
            "planned_pickup_date": "2026-08-10",
            "planned_delivery_date": "2026-08-12",
            "notes": "Belgian demo order",
            "stops": [
                {"stop_type": "PICKUP", "sequence": 1, "city": "Antwerp", "country": "BE"},
                {"stop_type": "DELIVERY", "sequence": 2, "city": "Brussels", "country": "BE"},
            ],
            "vehicles": [{"make": "BMW", "model": "320", "vin": "WBAPH5C55BA123456"}],
        },
    )
    assert create_response.status_code == 201
    order_id = create_response.json()["data"]["id"]

    assign_response = client.post(
        f"/api/v1/orders/{order_id}/assign-driver",
        headers=headers,
        json={
            "driver_id": drivers[0]["id"],
            "truck_id": trucks[0]["id"],
            "trailer_id": trailers[0]["id"],
        },
    )
    assert assign_response.status_code == 200
    assigned = assign_response.json()["data"]
    assert assigned["assigned_driver_id"] == drivers[0]["id"]
    assert assigned["assigned_truck_id"] == trucks[0]["id"]
    assert assigned["assigned_trailer_id"] == trailers[0]["id"]
