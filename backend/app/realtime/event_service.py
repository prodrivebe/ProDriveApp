"""Centralized realtime event publishing and delivery."""

from __future__ import annotations

import asyncio
import logging
import threading
import uuid
from typing import TYPE_CHECKING, Any

from app.realtime.connection_manager import ConnectionManager
from app.realtime.presence import PresenceService
from app.realtime.redis_events import InMemoryEventBridge, RedisEventBridge
from app.realtime.schemas import RealtimeEvent, RealtimeEventType

if TYPE_CHECKING:
    from redis import Redis

logger = logging.getLogger(__name__)

_event_service: EventService | None = None


class EventService:
    """Publish domain events and deliver them to websocket clients."""

    def __init__(
        self,
        connection_manager: ConnectionManager,
        presence: PresenceService,
        bridge: RedisEventBridge | InMemoryEventBridge,
    ) -> None:
        self._connection_manager = connection_manager
        self._presence = presence
        self._bridge = bridge
        self._loop: asyncio.AbstractEventLoop | None = None
        self._pending: list[RealtimeEvent] = []
        self._pending_lock = threading.Lock()
        self._flush_timer: threading.Timer | None = None
        self._batch_window_seconds = 0.05

    def bind_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """Bind the running asyncio loop for thread-safe delivery."""
        self._loop = loop

    def start(self) -> None:
        """Start Redis subscriber."""
        self._bridge.start()

    def stop(self) -> None:
        """Stop background workers."""
        if self._flush_timer is not None:
            self._flush_timer.cancel()
        self._bridge.stop()

    def publish(self, event: RealtimeEvent) -> None:
        """Queue an event for batched publish."""
        with self._pending_lock:
            self._pending.append(event)
            if self._flush_timer is None:
                self._flush_timer = threading.Timer(
                    self._batch_window_seconds,
                    self._flush_pending,
                )
                self._flush_timer.daemon = True
                self._flush_timer.start()

    def publish_now(self, event: RealtimeEvent) -> None:
        """Publish immediately without batching."""
        self._bridge.publish(event)

    def _flush_pending(self) -> None:
        with self._pending_lock:
            events = self._pending[:]
            self._pending.clear()
            self._flush_timer = None
        if not events:
            return
        self._bridge.publish_batch(events)

    def handle_incoming_event(self, event: RealtimeEvent) -> None:
        """Deliver an event received from Redis to local websocket clients."""
        if self._loop is None or self._loop.is_closed():
            logger.warning("Realtime loop not bound; dropping event %s", event.type)
            return

        async def _deliver() -> None:
            await self._connection_manager.broadcast_event(event)

        asyncio.run_coroutine_threadsafe(_deliver(), self._loop)

    async def maintenance(self) -> None:
        """Periodic cleanup for stale websocket connections."""
        await self._connection_manager.cleanup_stale_connections()


def build_event_service(
    *,
    redis_client: Redis | None,
    use_memory_bridge: bool = False,
) -> EventService:
    """Create event service with Redis or in-memory bridge."""
    connection_manager = ConnectionManager()
    if redis_client is None or use_memory_bridge:
        presence = PresenceService(_MemoryRedis())
        service = EventService(
            connection_manager,
            presence,
            InMemoryEventBridge(lambda event: service.handle_incoming_event(event)),
        )
        return service

    presence = PresenceService(redis_client)
    service = EventService(
        connection_manager,
        presence,
        RedisEventBridge(redis_client, lambda event: service.handle_incoming_event(event)),
    )
    return service


def init_event_service(
    *,
    redis_client: Redis | None,
    use_memory_bridge: bool = False,
) -> EventService:
    """Initialize global event service singleton."""
    global _event_service
    _event_service = build_event_service(
        redis_client=redis_client,
        use_memory_bridge=use_memory_bridge,
    )
    return _event_service


def get_event_service() -> EventService | None:
    """Return initialized event service if available."""
    return _event_service


class _MemoryRedis:
    """Minimal in-memory Redis stand-in for tests."""

    def __init__(self) -> None:
        self._hashes: dict[str, dict[str, str]] = {}

    def hset(self, key: str, field: str, value: str) -> None:
        self._hashes.setdefault(key, {})[field] = value

    def hget(self, key: str, field: str) -> str | None:
        return self._hashes.get(key, {}).get(field)

    def hgetall(self, key: str) -> dict[str, str]:
        return dict(self._hashes.get(key, {}))

    def hdel(self, key: str, field: str) -> None:
        if key in self._hashes:
            self._hashes[key].pop(field, None)

    def expire(self, key: str, seconds: int) -> None:
        _ = (key, seconds)

    def publish(self, channel: str, message: str) -> None:
        _ = (channel, message)

    def pubsub(self, ignore_subscribe_messages: bool = True) -> Any:
        _ = ignore_subscribe_messages
        return self

    def psubscribe(self, pattern: str) -> None:
        _ = pattern

    def get_message(self, timeout: float = 1.0) -> None:
        _ = timeout
        return None

    def close(self) -> None:
        return
