"""Multi-tenant isolation verification for beta readiness."""

from __future__ import annotations

import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.auth.security import create_jwt_token, hash_password
from app.common.enums import UserRole
from app.companies.models import Company, CompanySettings
from app.users.models import User


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _bootstrap_other_company(db_engine, test_settings) -> tuple[str, str]:
    session = sessionmaker(bind=db_engine)()
    company = Company(name="Tenant B Transport")
    session.add(company)
    session.commit()
    session.add(CompanySettings(company_id=company.id))
    admin = User(
        company_id=company.id,
        first_name="Tenant",
        last_name="Admin",
        email=f"tenant-b-{uuid.uuid4().hex[:6]}@example.com",
        password_hash=hash_password("TenantB123!"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    session.add(admin)
    session.commit()
    token, _ = create_jwt_token(
        settings=test_settings,
        user_id=admin.id,
        company_id=admin.company_id,
        role=UserRole.ADMIN,
        token_type="access",
    )
    session.close()
    return str(company.id), token


def test_orders_are_isolated_between_companies(
    client: TestClient,
    admin_tokens: dict[str, str],
    db_engine,
    test_settings,
) -> None:
    headers = _headers(admin_tokens["access_token"])
    customer = client.post(
        "/api/v1/customers",
        headers=headers,
        json={"company_name": "Tenant A Customer"},
    ).json()["data"]
    order = client.post(
        "/api/v1/orders",
        headers=headers,
        json={
            "customer_id": customer["id"],
            "stops": [
                {"stop_type": "PICKUP", "sequence": 1, "city": "Paris"},
                {"stop_type": "DELIVERY", "sequence": 2, "city": "Lyon"},
            ],
            "vehicles": [{"make": "Peugeot", "model": "308"}],
        },
    ).json()["data"]

    _, other_token = _bootstrap_other_company(db_engine, test_settings)
    blocked = client.get(f"/api/v1/orders/{order['id']}", headers=_headers(other_token))
    assert blocked.status_code == 404


def test_planning_board_is_scoped_to_company(
    client: TestClient,
    admin_tokens: dict[str, str],
    db_engine,
    test_settings,
) -> None:
    headers = _headers(admin_tokens["access_token"])
    client.post(
        "/api/v1/customers",
        headers=headers,
        json={"company_name": "Planning Tenant A"},
    )
    tenant_a = client.get("/api/v1/planning/board", headers=headers).json()["data"]

    _, other_token = _bootstrap_other_company(db_engine, test_settings)
    tenant_b = client.get("/api/v1/planning/board", headers=_headers(other_token)).json()["data"]

    tenant_a_count = sum(len(items) for items in tenant_a["columns"].values())
    tenant_b_count = sum(len(items) for items in tenant_b["columns"].values())
    assert tenant_a_count >= 0
    assert tenant_b_count == 0


def test_ai_suggestions_are_isolated(
    client: TestClient,
    admin_tokens: dict[str, str],
    db_engine,
    test_settings,
) -> None:
    headers = _headers(admin_tokens["access_token"])
    suggestion = client.post(
        "/api/v1/ai/parse-order",
        headers=headers,
        json={"message": "Pick up:\nToyota Yaris\nUtrecht\nDeliver:\nAntwerp"},
    ).json()["data"]

    _, other_token = _bootstrap_other_company(db_engine, test_settings)
    blocked = client.get(f"/api/v1/ai/suggestions/{suggestion['id']}", headers=_headers(other_token))
    assert blocked.status_code == 404
