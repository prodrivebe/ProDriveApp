"""Authenticated websocket endpoints."""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from typing import Any

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

from app.auth.security import decode_jwt_token
from app.common.enums import UserRole
from app.config.settings import Settings, get_settings
from app.realtime.event_service import get_event_service
from app.realtime.publisher import publish_presence_updated
from app.realtime.schemas import RealtimeChannelKind, RealtimeEventType, logical_channel

logger = logging.getLogger(__name__)

router = APIRouter(tags=["realtime"])


def _default_channels(
    *,
    company_id: uuid.UUID,
    user_id: uuid.UUID,
    role: UserRole,
) -> set[str]:
    channels = {
        logical_channel(RealtimeChannelKind.COMPANY, company_id=company_id),
        logical_channel(RealtimeChannelKind.NOTIFICATIONS, company_id=company_id, user_id=user_id),
    }
    if role in {UserRole.ADMIN, UserRole.DISPATCHER}:
        channels.add(logical_channel(RealtimeChannelKind.DISPATCHER, company_id=company_id))
    if role == UserRole.DRIVER:
        channels.add(logical_channel(RealtimeChannelKind.DRIVER, company_id=company_id, user_id=user_id))
    return channels


def _authenticate_token(token: str, settings: Settings) -> tuple[uuid.UUID, uuid.UUID, UserRole]:
    payload = decode_jwt_token(token, settings)
    if payload.get("type") != "access":
        raise ValueError("Access token required.")
    return (
        uuid.UUID(payload["sub"]),
        uuid.UUID(payload["company_id"]),
        UserRole(payload["role"]),
    )


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(..., description="JWT access token"),
) -> None:
    """Authenticated realtime websocket."""
    settings = get_settings()
    service = get_event_service()
    if service is None:
        await websocket.close(code=1013)
        return

    try:
        user_id, company_id, role = _authenticate_token(token, settings)
    except Exception:
        await websocket.close(code=4401)
        return

    connection = await service._connection_manager.connect(
        websocket,
        user_id=user_id,
        company_id=company_id,
        role=role,
        default_channels=_default_channels(
            company_id=company_id,
            user_id=user_id,
            role=role,
        ),
    )

    presence_status = "online"
    if role == UserRole.DRIVER:
        presence_status = "available"
    service._presence.mark_online(
        company_id=company_id,
        user_id=user_id,
        role=role,
        status=presence_status,
    )
    publish_presence_updated(
        company_id=company_id,
        user_id=user_id,
        role=role,
        status=presence_status,
    )
    if role == UserRole.DRIVER:
        from app.realtime.publisher import publish_driver_connection

        publish_driver_connection(
            company_id=company_id,
            user_id=user_id,
            connected=True,
        )

    heartbeat_task = asyncio.create_task(_heartbeat_loop(service, connection.connection_id))

    try:
        while websocket.client_state == WebSocketState.CONNECTED:
            message = await websocket.receive_text()
            await service._connection_manager.touch(connection.connection_id)
            await _handle_client_message(service, connection.connection_id, company_id, message)
    except WebSocketDisconnect:
        pass
    finally:
        heartbeat_task.cancel()
        await service._connection_manager.disconnect(connection.connection_id)
        service._presence.mark_offline(company_id=company_id, user_id=user_id)
        publish_presence_updated(
            company_id=company_id,
            user_id=user_id,
            role=role,
            status="offline",
        )
        if role == UserRole.DRIVER:
            from app.realtime.publisher import publish_driver_connection

            publish_driver_connection(
                company_id=company_id,
                user_id=user_id,
                connected=False,
            )


async def _heartbeat_loop(service: Any, connection_id: str) -> None:
    while True:
        await asyncio.sleep(30)
        await service._connection_manager.send_heartbeat(connection_id)


async def _handle_client_message(
    service: Any,
    connection_id: str,
    company_id: uuid.UUID,
    raw_message: str,
) -> None:
    try:
        payload = json.loads(raw_message)
    except json.JSONDecodeError:
        return

    action = payload.get("action")
    if action == "ping":
        await service._connection_manager.send_json(
            connection_id,
            {"type": RealtimeEventType.HEARTBEAT.value, "action": "pong"},
        )
        return

    if action == "subscribe":
        channel_kind = payload.get("channel")
        if channel_kind == "order" and payload.get("order_id"):
            channel = logical_channel(
                RealtimeChannelKind.ORDER,
                company_id=company_id,
                order_id=uuid.UUID(str(payload["order_id"])),
            )
            await service._connection_manager.subscribe(connection_id, channel)
        return

    if action == "presence":
        status = str(payload.get("status", "online"))
        info = service._connection_manager._connections.get(connection_id)
        if info is None:
            return
        service._presence.touch(company_id=company_id, user_id=info.user_id, status=status)
        publish_presence_updated(
            company_id=company_id,
            user_id=info.user_id,
            role=info.role,
            status=status,
            active_order_id=(
                uuid.UUID(str(payload["active_order_id"]))
                if payload.get("active_order_id")
                else None
            ),
        )
