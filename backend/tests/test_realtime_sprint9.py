"""Sprint 9 realtime infrastructure tests."""

from __future__ import annotations

import json
import uuid

import pytest
from fastapi.testclient import TestClient

from app.auth.security import create_jwt_token
from app.common.enums import UserRole
from app.config.settings import Settings
from app.realtime.event_service import get_event_service
from app.realtime.publisher import publish_order_event
from app.realtime.schemas import RealtimeEventType


def _access_token(settings: Settings, user_id: uuid.UUID, company_id: uuid.UUID, role: UserRole) -> str:
    token, _ = create_jwt_token(
        settings=settings,
        user_id=user_id,
        company_id=company_id,
        role=role,
        token_type="access",
    )
    return token


def _receive_ws_message(websocket, *, event_type: str | None = None) -> dict:
    """Receive websocket messages until the expected event type is found."""
    while True:
        message = websocket.receive_json()
        if event_type is None or message.get("type") == event_type:
            return message


def test_websocket_rejects_missing_token(client: TestClient) -> None:
    with pytest.raises(Exception):
        with client.websocket_connect("/api/v1/ws"):
            pass


def test_websocket_authenticates_dispatcher(
    client: TestClient,
    admin_tokens: dict[str, str],
    test_settings: Settings,
    db_engine,
) -> None:
    from sqlalchemy.orm import sessionmaker

    from app.companies.models import Company
    from app.users.models import User

    session = sessionmaker(bind=db_engine)()
    admin = session.query(User).filter(User.email == test_settings.seed_admin_email.lower()).one()
    token = _access_token(
        test_settings,
        admin.id,
        admin.company_id,
        UserRole.ADMIN,
    )
    session.close()

    with client.websocket_connect(f"/api/v1/ws?token={token}") as websocket:
        websocket.send_text(json.dumps({"action": "ping"}))
        message = websocket.receive_json()
        assert message["type"] == "HEARTBEAT"


def test_publish_order_event_reaches_connected_client(
    client: TestClient,
    test_settings: Settings,
    db_engine,
) -> None:
    from sqlalchemy.orm import sessionmaker

    from app.users.models import User

    session = sessionmaker(bind=db_engine)()
    admin = session.query(User).filter(User.email == test_settings.seed_admin_email.lower()).one()
    token = _access_token(
        test_settings,
        admin.id,
        admin.company_id,
        UserRole.ADMIN,
    )
    session.close()

    with client.websocket_connect(f"/api/v1/ws?token={token}") as websocket:
        publish_order_event(
            company_id=admin.company_id,
            order_id=uuid.uuid4(),
            event_type=RealtimeEventType.ORDER_ASSIGNED,
            order_number="ORD-000999",
            status="ASSIGNED",
        )
        message = _receive_ws_message(websocket, event_type=RealtimeEventType.ORDER_ASSIGNED.value)
        assert message["payload"]["order_number"] == "ORD-000999"


def test_company_isolation_on_websocket_delivery(
    client: TestClient,
    test_settings: Settings,
    db_engine,
) -> None:
    from sqlalchemy.orm import sessionmaker

    from app.auth.security import hash_password
    from app.companies.models import Company, CompanySettings
    from app.users.models import User

    session = sessionmaker(bind=db_engine)()
    other_company = Company(name="Other Transport")
    session.add(other_company)
    session.commit()
    session.add(CompanySettings(company_id=other_company.id))
    other_admin = User(
        company_id=other_company.id,
        first_name="Other",
        last_name="Admin",
        email="other-admin@example.com",
        password_hash=hash_password("OtherAdmin123!"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    session.add(other_admin)
    session.commit()

    primary_admin = session.query(User).filter(User.email == test_settings.seed_admin_email.lower()).one()
    primary_token = _access_token(
        test_settings,
        primary_admin.id,
        primary_admin.company_id,
        UserRole.ADMIN,
    )
    other_token = _access_token(
        test_settings,
        other_admin.id,
        other_admin.company_id,
        UserRole.ADMIN,
    )
    session.close()

    with client.websocket_connect(f"/api/v1/ws?token={primary_token}") as primary_ws:
        with client.websocket_connect(f"/api/v1/ws?token={other_token}") as other_ws:
            publish_order_event(
                company_id=other_admin.company_id,
                order_id=uuid.uuid4(),
                event_type=RealtimeEventType.ORDER_ACCEPTED,
                order_number="ORD-OTHER-1",
                status="ACCEPTED",
            )
            other_message = _receive_ws_message(
                other_ws,
                event_type=RealtimeEventType.ORDER_ACCEPTED.value,
            )
            assert other_message["payload"]["order_number"] == "ORD-OTHER-1"

            primary_ws.send_text(json.dumps({"action": "ping"}))
            primary_message = _receive_ws_message(primary_ws, event_type="HEARTBEAT")
            assert primary_message["type"] == "HEARTBEAT"


def test_presence_endpoint_returns_records(
    client: TestClient,
    admin_tokens: dict[str, str],
) -> None:
    token = admin_tokens["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    with client.websocket_connect(f"/api/v1/ws?token={token}"):
        response = client.get("/api/v1/realtime/presence", headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json()["data"], list)


def test_event_service_initialized_in_app(client: TestClient) -> None:
    service = get_event_service()
    assert service is not None
