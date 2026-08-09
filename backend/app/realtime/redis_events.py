"""Redis pub/sub bridge for realtime events."""

from __future__ import annotations

import json
import logging
import threading
from typing import TYPE_CHECKING, Callable

from app.realtime.schemas import RealtimeEvent, redis_company_channel

if TYPE_CHECKING:
    from redis import Redis

    from app.realtime.connection_manager import ConnectionManager

logger = logging.getLogger(__name__)


class RedisEventBridge:
    """Publish events to Redis and fan-out to local websocket connections."""

    def __init__(
        self,
        redis_client: Redis,
        on_event: Callable[[RealtimeEvent], None],
    ) -> None:
        self._redis = redis_client
        self._on_event = on_event
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    def publish(self, event: RealtimeEvent) -> None:
        """Publish an event to the company Redis channel."""
        channel = redis_company_channel(event.company_id)
        self._redis.publish(channel, event.model_dump_json())

    def publish_batch(self, events: list[RealtimeEvent]) -> None:
        """Publish multiple events."""
        for event in events:
            self.publish(event)

    def start(self) -> None:
        """Start background Redis subscription thread."""
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._listen, name="realtime-redis", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop background subscription thread."""
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=2)
            self._thread = None

    def _listen(self) -> None:
        pubsub = self._redis.pubsub(ignore_subscribe_messages=True)
        pubsub.psubscribe("prodrive:events:*")
        logger.info("Realtime Redis subscriber started")
        while not self._stop_event.is_set():
            message = pubsub.get_message(timeout=1.0)
            if message is None:
                continue
            if message.get("type") not in {"message", "pmessage"}:
                continue
            data = message.get("data")
            if not isinstance(data, str):
                continue
            try:
                payload = json.loads(data)
                event = RealtimeEvent.model_validate(payload)
                self._on_event(event)
            except Exception:
                logger.exception("Failed to process realtime Redis message")
        pubsub.close()
        logger.info("Realtime Redis subscriber stopped")


class InMemoryEventBridge:
    """Fallback bridge for tests without Redis."""

    def __init__(self, on_event: Callable[[RealtimeEvent], None]) -> None:
        self._on_event = on_event

    def publish(self, event: RealtimeEvent) -> None:
        self._on_event(event)

    def publish_batch(self, events: list[RealtimeEvent]) -> None:
        for event in events:
            self.publish(event)

    def start(self) -> None:
        return

    def stop(self) -> None:
        return
