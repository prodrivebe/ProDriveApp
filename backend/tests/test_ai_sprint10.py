"""Sprint 10 AI-assisted dispatching tests."""

from __future__ import annotations

import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from app.ai.models.ai_suggestion import AIAuditLog, AISuggestion
from app.common.enums import AISuggestionStatus, AISuggestionType


def _create_customer(client: TestClient, headers: dict[str, str]) -> str:
    response = client.post(
        "/api/v1/customers",
        headers=headers,
        json={"company_name": "AI Test Customer", "email": "ai-customer@example.com"},
    )
    assert response.status_code == 201
    return response.json()["data"]["id"]


def test_parse_order_creates_pending_suggestion_with_confidence(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
    response = client.post(
        "/api/v1/ai/parse-order",
        headers=headers,
        json={
            "message": "Customer: ACME Logistics\nPick up:\nBMW X5\nAmsterdam\nDeliver:\nBrussels",
        },
    )
    assert response.status_code == 200
    suggestion = response.json()["data"]
    assert suggestion["status"] == AISuggestionStatus.PENDING.value
    assert suggestion["suggestion_type"] == AISuggestionType.ORDER_PARSE.value
    assert suggestion["confidence"] > 0
    assert "field_confidence" in suggestion["output_json"]
    assert suggestion["output_json"]["field_confidence"]["customer_name"] >= 0.9


def test_approve_order_suggestion_creates_real_order(
    client: TestClient,
    admin_tokens: dict[str, str],
    db_engine,
) -> None:
    headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
    customer_id = _create_customer(client, headers)
    parse_response = client.post(
        "/api/v1/ai/parse-order",
        headers=headers,
        json={"message": "Pick up:\nBMW X5\nAmsterdam\nDeliver:\nBrussels"},
    )
    suggestion_id = parse_response.json()["data"]["id"]

    approve_response = client.post(
        f"/api/v1/ai/suggestions/{suggestion_id}/approve",
        headers=headers,
        json={"customer_id": customer_id},
    )
    assert approve_response.status_code == 200
    approved = approve_response.json()["data"]
    assert approved["status"] == AISuggestionStatus.APPROVED.value
    assert approved["output_json"]["created_order_id"]

    order_id = approved["output_json"]["created_order_id"]
    order_response = client.get(f"/api/v1/orders/{order_id}", headers=headers)
    assert order_response.status_code == 200

    session = sessionmaker(bind=db_engine)()
    audits = session.query(AIAuditLog).filter(AIAuditLog.suggestion_id == uuid.UUID(suggestion_id)).all()
    assert any(item.event_type == "REQUEST" for item in audits)
    assert any(item.event_type == "RESPONSE" for item in audits)
    assert any(item.event_type == "APPROVED" for item in audits)
    session.close()


def test_reject_suggestion_tracks_decision(
    client: TestClient,
    admin_tokens: dict[str, str],
    db_engine,
) -> None:
    headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
    parse_response = client.post(
        "/api/v1/ai/parse-order",
        headers=headers,
        json={"message": "Pick up:\nAudi A4\nRotterdam\nDeliver:\nParis"},
    )
    suggestion_id = parse_response.json()["data"]["id"]
    reject_response = client.post(
        f"/api/v1/ai/suggestions/{suggestion_id}/reject",
        headers=headers,
        json={"reason": "Incomplete delivery details"},
    )
    assert reject_response.status_code == 200
    assert reject_response.json()["data"]["status"] == AISuggestionStatus.REJECTED.value

    session = sessionmaker(bind=db_engine)()
    audits = session.query(AIAuditLog).filter(AIAuditLog.suggestion_id == uuid.UUID(suggestion_id)).all()
    assert any(item.event_type == "REJECTED" for item in audits)
    session.close()


def test_recommend_driver_creates_suggestion_with_reasoning(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
    customer_id = _create_customer(client, headers)
    order_response = client.post(
        "/api/v1/ai/parse-order",
        headers=headers,
        json={"message": "Pick up:\nBMW X5\nAmsterdam\nDeliver:\nBrussels"},
    )
    suggestion_id = order_response.json()["data"]["id"]
    approve_response = client.post(
        f"/api/v1/ai/suggestions/{suggestion_id}/approve",
        headers=headers,
        json={"customer_id": customer_id},
    )
    order_id = approve_response.json()["data"]["output_json"]["created_order_id"]

    recommend_response = client.post(
        "/api/v1/ai/recommend-driver",
        headers=headers,
        json={"order_id": order_id},
    )
    assert recommend_response.status_code == 200
    suggestion = recommend_response.json()["data"]
    assert suggestion["suggestion_type"] == AISuggestionType.DRIVER_RECOMMENDATION.value
    recommended = suggestion["output_json"]["recommended"]
    assert recommended is None or "reasons" in recommended


def test_company_isolation_for_suggestions(
    client: TestClient,
    admin_tokens: dict[str, str],
    test_settings,
    db_engine,
) -> None:
    from app.auth.security import hash_password
    from app.companies.models import Company, CompanySettings
    from app.users.models import User

    headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
    parse_response = client.post(
        "/api/v1/ai/parse-order",
        headers=headers,
        json={"message": "Pick up:\nVW Golf\nBerlin\nDeliver:\nMunich"},
    )
    suggestion_id = parse_response.json()["data"]["id"]

    session = sessionmaker(bind=db_engine)()
    other_company = Company(name="Other AI Co")
    session.add(other_company)
    session.commit()
    session.add(CompanySettings(company_id=other_company.id))
    other_admin = User(
        company_id=other_company.id,
        first_name="Other",
        last_name="Admin",
        email="other-ai@example.com",
        password_hash=hash_password("OtherAdmin123!"),
        role="ADMIN",
        is_active=True,
    )
    session.add(other_admin)
    session.commit()

    from app.auth.security import create_jwt_token
    from app.common.enums import UserRole

    token, _ = create_jwt_token(
        settings=test_settings,
        user_id=other_admin.id,
        company_id=other_admin.company_id,
        role=UserRole.ADMIN,
        token_type="access",
    )
    session.close()

    other_headers = {"Authorization": f"Bearer {token}"}
    blocked = client.get(f"/api/v1/ai/suggestions/{suggestion_id}", headers=other_headers)
    assert blocked.status_code == 404


def test_list_suggestions_returns_company_records(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    headers = {"Authorization": f"Bearer {admin_tokens['access_token']}"}
    client.post(
        "/api/v1/ai/parse-order",
        headers=headers,
        json={"message": "Pick up:\nToyota Yaris\nUtrecht\nDeliver:\nAntwerp"},
    )
    list_response = client.get("/api/v1/ai/suggestions", headers=headers)
    assert list_response.status_code == 200
    assert len(list_response.json()["data"]) >= 1
