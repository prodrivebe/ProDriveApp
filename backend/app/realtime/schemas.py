"""Realtime event schemas and channel helpers."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class RealtimeChannelKind(StrEnum):
    """Logical channel types exposed to clients."""

    COMPANY = "company"
    DISPATCHER = "dispatcher"
    DRIVER = "driver"
    ORDER = "order"
    NOTIFICATIONS = "notifications"


class RealtimeEventType(StrEnum):
    """Domain events broadcast to connected clients."""

    ORDER_ASSIGNED = "ORDER_ASSIGNED"
    ORDER_ACCEPTED = "ORDER_ACCEPTED"
    ORDER_REJECTED = "ORDER_REJECTED"
    DRIVER_ARRIVED_PICKUP = "DRIVER_ARRIVED_PICKUP"
    LOADING_STARTED = "LOADING_STARTED"
    LOADING_COMPLETED = "LOADING_COMPLETED"
    TRANSIT_STARTED = "TRANSIT_STARTED"
    ARRIVED_DELIVERY = "ARRIVED_DELIVERY"
    DELIVERY_STARTED = "DELIVERY_STARTED"
    ORDER_COMPLETED = "ORDER_COMPLETED"
    VIN_VERIFIED = "VIN_VERIFIED"
    VIN_CHANGED = "VIN_CHANGED"
    PHOTO_UPLOADED = "PHOTO_UPLOADED"
    DAMAGE_REPORTED = "DAMAGE_REPORTED"
    CMR_UPLOADED = "CMR_UPLOADED"
    DOCUMENT_UPLOADED = "DOCUMENT_UPLOADED"
    DRIVER_CONNECTED = "DRIVER_CONNECTED"
    DRIVER_DISCONNECTED = "DRIVER_DISCONNECTED"
    TIMELINE_ENTRY = "TIMELINE_ENTRY"
    NOTIFICATION_CREATED = "NOTIFICATION_CREATED"
    PRESENCE_UPDATED = "PRESENCE_UPDATED"
    ORDER_UPDATED = "ORDER_UPDATED"
    HEARTBEAT = "HEARTBEAT"


class RealtimeEvent(BaseModel):
    """Wire format for realtime messages."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: RealtimeEventType
    company_id: str
    channel: str
    payload: dict[str, Any] = Field(default_factory=dict)
    severity: str = "info"
    created_at: str = Field(default_factory=lambda: datetime.now(tz=UTC).isoformat())

    def model_dump_json(self, **kwargs: Any) -> str:
        return super().model_dump_json(by_alias=True, **kwargs)


def redis_company_channel(company_id: uuid.UUID | str) -> str:
    """Redis pub/sub channel for a company."""
    return f"prodrive:events:{company_id}"


def logical_channel(
    kind: RealtimeChannelKind,
    *,
    company_id: uuid.UUID | str,
    user_id: uuid.UUID | str | None = None,
    order_id: uuid.UUID | str | None = None,
) -> str:
    """Build a logical channel name delivered to websocket clients."""
    if kind == RealtimeChannelKind.COMPANY:
        return f"company:{company_id}"
    if kind == RealtimeChannelKind.DISPATCHER:
        return f"dispatcher:{company_id}"
    if kind == RealtimeChannelKind.DRIVER:
        return f"driver:{user_id}"
    if kind == RealtimeChannelKind.ORDER:
        return f"order:{order_id}"
    if kind == RealtimeChannelKind.NOTIFICATIONS:
        return f"notifications:{user_id}"
    raise ValueError(f"Unsupported channel kind: {kind}")
