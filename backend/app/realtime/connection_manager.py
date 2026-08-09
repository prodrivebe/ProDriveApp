"""In-memory WebSocket connection registry."""

from __future__ import annotations

import asyncio
import logging
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime

from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect

from app.common.enums import UserRole
from app.realtime.schemas import RealtimeEvent, RealtimeEventType

logger = logging.getLogger(__name__)

MAX_CONNECTIONS_PER_USER = 5
STALE_CONNECTION_SECONDS = 90


@dataclass
class ConnectionInfo:
    """Metadata for an authenticated websocket connection."""

    connection_id: str
    websocket: WebSocket
    user_id: uuid.UUID
    company_id: uuid.UUID
    role: UserRole
    subscribed_channels: set[str] = field(default_factory=set)
    connected_at: datetime = field(default_factory=lambda: datetime.now(tz=UTC))
    last_seen_at: datetime = field(default_factory=lambda: datetime.now(tz=UTC))


class ConnectionManager:
    """Track websocket connections and deliver channel messages."""

    def __init__(self) -> None:
        self._connections: dict[str, ConnectionInfo] = {}
        self._by_user: dict[uuid.UUID, set[str]] = defaultdict(set)
        self._by_company: dict[uuid.UUID, set[str]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(
        self,
        websocket: WebSocket,
        *,
        user_id: uuid.UUID,
        company_id: uuid.UUID,
        role: UserRole,
        default_channels: set[str],
    ) -> ConnectionInfo:
        """Accept and register a websocket connection."""
        await websocket.accept()
        async with self._lock:
            existing = self._by_user.get(user_id, set())
            if len(existing) >= MAX_CONNECTIONS_PER_USER:
                oldest = min(
                    (self._connections[cid] for cid in existing),
                    key=lambda item: item.connected_at,
                )
                await self.disconnect(oldest.connection_id)

            connection_id = str(uuid.uuid4())
            info = ConnectionInfo(
                connection_id=connection_id,
                websocket=websocket,
                user_id=user_id,
                company_id=company_id,
                role=role,
                subscribed_channels=set(default_channels),
            )
            self._connections[connection_id] = info
            self._by_user[user_id].add(connection_id)
            self._by_company[company_id].add(connection_id)
            return info

    async def disconnect(self, connection_id: str) -> ConnectionInfo | None:
        """Remove a websocket connection."""
        async with self._lock:
            info = self._connections.pop(connection_id, None)
            if info is None:
                return None
            self._by_user[info.user_id].discard(connection_id)
            if not self._by_user[info.user_id]:
                del self._by_user[info.user_id]
            self._by_company[info.company_id].discard(connection_id)
            if not self._by_company[info.company_id]:
                del self._by_company[info.company_id]
        try:
            await info.websocket.close()
        except (RuntimeError, WebSocketDisconnect):
            pass
        return info

    async def subscribe(self, connection_id: str, channel: str) -> None:
        """Subscribe a connection to an additional logical channel."""
        async with self._lock:
            info = self._connections.get(connection_id)
            if info is not None:
                info.subscribed_channels.add(channel)

    async def touch(self, connection_id: str) -> None:
        """Update last seen timestamp for heartbeat handling."""
        async with self._lock:
            info = self._connections.get(connection_id)
            if info is not None:
                info.last_seen_at = datetime.now(tz=UTC)

    async def send_json(self, connection_id: str, payload: dict[str, object]) -> None:
        """Send JSON payload to one connection."""
        info = self._connections.get(connection_id)
        if info is None:
            return
        try:
            await info.websocket.send_json(payload)
            await self.touch(connection_id)
        except (RuntimeError, WebSocketDisconnect):
            await self.disconnect(connection_id)

    async def broadcast_event(self, event: RealtimeEvent) -> int:
        """Deliver an event to subscribed connections within the same company."""
        payload = event.model_dump(mode="json")
        delivered = 0
        connection_ids = list(self._connections.keys())
        for connection_id in connection_ids:
            info = self._connections.get(connection_id)
            if info is None:
                continue
            if str(info.company_id) != event.company_id:
                continue
            if not self._should_receive(info, event.channel):
                continue
            await self.send_json(connection_id, payload)
            delivered += 1
        return delivered

    async def broadcast_batch(self, events: list[RealtimeEvent]) -> int:
        """Deliver multiple events efficiently."""
        if not events:
            return 0
        batched: dict[str, list[dict[str, object]]] = defaultdict(list)
        for event in events:
            payload = event.model_dump(mode="json")
            for connection_id, info in list(self._connections.items()):
                if str(info.company_id) != event.company_id:
                    continue
                if self._should_receive(info, event.channel):
                    batched[connection_id].append(payload)

        delivered = 0
        for connection_id, payloads in batched.items():
            if len(payloads) == 1:
                await self.send_json(connection_id, payloads[0])
            else:
                await self.send_json(connection_id, {"type": "BATCH", "events": payloads})
            delivered += len(payloads)
        return delivered

    def list_company_connections(self, company_id: uuid.UUID) -> list[ConnectionInfo]:
        """Return active connections for a company."""
        ids = self._by_company.get(company_id, set())
        return [self._connections[cid] for cid in ids if cid in self._connections]

    def count_online_users(self, company_id: uuid.UUID, role: UserRole | None = None) -> int:
        """Count distinct online users for a company."""
        users: set[uuid.UUID] = set()
        for info in self.list_company_connections(company_id):
            if role is None or info.role == role:
                users.add(info.user_id)
        return len(users)

    async def cleanup_stale_connections(self) -> int:
        """Disconnect connections that missed heartbeats."""
        now = datetime.now(tz=UTC)
        stale = [
            connection_id
            for connection_id, info in self._connections.items()
            if (now - info.last_seen_at).total_seconds() > STALE_CONNECTION_SECONDS
        ]
        for connection_id in stale:
            await self.disconnect(connection_id)
        return len(stale)

    @staticmethod
    def _should_receive(info: ConnectionInfo, channel: str) -> bool:
        if channel in info.subscribed_channels:
            return True
        if channel.startswith("order:"):
            company_channel = f"company:{info.company_id}"
            dispatcher_channel = f"dispatcher:{info.company_id}"
            return company_channel in info.subscribed_channels or (
                info.role in {UserRole.ADMIN, UserRole.DISPATCHER}
                and dispatcher_channel in info.subscribed_channels
            )
        return False

    async def send_heartbeat(self, connection_id: str) -> None:
        """Send server heartbeat ping."""
        await self.send_json(
            connection_id,
            {
                "type": RealtimeEventType.HEARTBEAT.value,
                "timestamp": datetime.now(tz=UTC).isoformat(),
            },
        )
