"""Domain event publishing helpers for business services."""

from __future__ import annotations

import uuid
from typing import Any

from app.common.enums import UserRole
from app.realtime.event_service import get_event_service
from app.realtime.schemas import (
    RealtimeChannelKind,
    RealtimeEvent,
    RealtimeEventType,
    logical_channel,
)


def _severity_for_type(event_type: RealtimeEventType) -> str:
    if event_type in {
        RealtimeEventType.ORDER_REJECTED,
        RealtimeEventType.DAMAGE_REPORTED,
    }:
        return "warning"
    if event_type in {RealtimeEventType.ORDER_COMPLETED, RealtimeEventType.ORDER_ACCEPTED}:
        return "success"
    return "info"


def _publish_to_channels(
    *,
    company_id: uuid.UUID,
    event_type: RealtimeEventType,
    payload: dict[str, Any],
    channels: list[tuple[RealtimeChannelKind, dict[str, Any]]],
    severity: str | None = None,
) -> None:
    service = get_event_service()
    if service is None:
        return

    company_key = {"company_id": company_id}
    for kind, extra in channels:
        channel = logical_channel(kind, **{**company_key, **extra})
        event = RealtimeEvent(
            type=event_type,
            company_id=str(company_id),
            channel=channel,
            payload=payload,
            severity=severity or _severity_for_type(event_type),
        )
        service.publish(event)


def publish_order_event(
    *,
    company_id: uuid.UUID,
    order_id: uuid.UUID,
    event_type: RealtimeEventType,
    order_number: str,
    status: str,
    driver_user_id: uuid.UUID | None = None,
    extra: dict[str, Any] | None = None,
) -> None:
    """Publish an order lifecycle event."""
    payload = {
        "order_id": str(order_id),
        "order_number": order_number,
        "status": status,
        **(extra or {}),
    }
    channels: list[tuple[RealtimeChannelKind, dict[str, Any]]] = [
        (RealtimeChannelKind.COMPANY, {}),
        (RealtimeChannelKind.DISPATCHER, {}),
        (RealtimeChannelKind.ORDER, {"order_id": order_id}),
    ]
    if driver_user_id is not None:
        channels.append((RealtimeChannelKind.DRIVER, {"user_id": driver_user_id}))
    _publish_to_channels(
        company_id=company_id,
        event_type=event_type,
        payload=payload,
        channels=channels,
    )


def publish_timeline_entry(
    *,
    company_id: uuid.UUID,
    order_id: uuid.UUID,
    entry_id: uuid.UUID,
    event_type: str,
    description: str,
    created_at: str,
) -> None:
    """Publish a timeline entry for live order detail views."""
    payload = {
        "order_id": str(order_id),
        "entry_id": str(entry_id),
        "event_type": event_type,
        "description": description,
        "created_at": created_at,
    }
    _publish_to_channels(
        company_id=company_id,
        event_type=RealtimeEventType.TIMELINE_ENTRY,
        payload=payload,
        channels=[
            (RealtimeChannelKind.COMPANY, {}),
            (RealtimeChannelKind.DISPATCHER, {}),
            (RealtimeChannelKind.ORDER, {"order_id": order_id}),
        ],
    )


def publish_notification_created(
    *,
    company_id: uuid.UUID,
    user_id: uuid.UUID,
    notification_id: uuid.UUID,
    title: str,
    message: str,
    notification_type: str,
    order_id: uuid.UUID | None = None,
) -> None:
    """Publish a notification event to a user's channel."""
    payload = {
        "notification_id": str(notification_id),
        "title": title,
        "message": message,
        "notification_type": notification_type,
        "order_id": str(order_id) if order_id else None,
    }
    _publish_to_channels(
        company_id=company_id,
        event_type=RealtimeEventType.NOTIFICATION_CREATED,
        payload=payload,
        channels=[
            (RealtimeChannelKind.NOTIFICATIONS, {"user_id": user_id}),
            (RealtimeChannelKind.DISPATCHER, {}),
        ],
        severity=_notification_severity(notification_type),
    )


def publish_presence_updated(
    *,
    company_id: uuid.UUID,
    user_id: uuid.UUID,
    role: UserRole,
    status: str,
    active_order_id: uuid.UUID | None = None,
) -> None:
    """Broadcast presence changes to dispatchers."""
    payload = {
        "user_id": str(user_id),
        "role": role.value,
        "status": status,
        "active_order_id": str(active_order_id) if active_order_id else None,
    }
    _publish_to_channels(
        company_id=company_id,
        event_type=RealtimeEventType.PRESENCE_UPDATED,
        payload=payload,
        channels=[
            (RealtimeChannelKind.COMPANY, {}),
            (RealtimeChannelKind.DISPATCHER, {}),
        ],
    )


def publish_vehicle_execution_event(
    *,
    company_id: uuid.UUID,
    order_id: uuid.UUID,
    event_type: RealtimeEventType,
    order_number: str,
    vehicle_id: uuid.UUID | None = None,
    extra: dict[str, Any] | None = None,
    driver_user_id: uuid.UUID | None = None,
) -> None:
    """Publish VIN/photo/damage/document execution events."""
    payload = {
        "order_id": str(order_id),
        "order_number": order_number,
        **(extra or {}),
    }
    if vehicle_id is not None:
        payload["vehicle_id"] = str(vehicle_id)
    channels: list[tuple[RealtimeChannelKind, dict[str, Any]]] = [
        (RealtimeChannelKind.COMPANY, {}),
        (RealtimeChannelKind.DISPATCHER, {}),
        (RealtimeChannelKind.ORDER, {"order_id": order_id}),
    ]
    if driver_user_id is not None:
        channels.append((RealtimeChannelKind.DRIVER, {"user_id": driver_user_id}))
    _publish_to_channels(
        company_id=company_id,
        event_type=event_type,
        payload=payload,
        channels=channels,
    )


def publish_driver_connection(
    *,
    company_id: uuid.UUID,
    user_id: uuid.UUID,
    connected: bool,
) -> None:
    """Publish driver online/offline connection events."""
    event_type = (
        RealtimeEventType.DRIVER_CONNECTED
        if connected
        else RealtimeEventType.DRIVER_DISCONNECTED
    )
    payload = {"user_id": str(user_id)}
    _publish_to_channels(
        company_id=company_id,
        event_type=event_type,
        payload=payload,
        channels=[
            (RealtimeChannelKind.COMPANY, {}),
            (RealtimeChannelKind.DISPATCHER, {}),
            (RealtimeChannelKind.DRIVER, {"user_id": user_id}),
        ],
    )


def _notification_severity(notification_type: str) -> str:
    lowered = notification_type.lower()
    if "reject" in lowered or "damage" in lowered or "delay" in lowered:
        return "warning"
    if "complete" in lowered or "accept" in lowered:
        return "success"
    if "error" in lowered or "fail" in lowered:
        return "error"
    return "info"
