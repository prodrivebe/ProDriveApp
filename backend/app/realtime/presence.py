"""Online presence tracking in Redis."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from app.common.enums import UserRole

if TYPE_CHECKING:
    from redis import Redis


PRESENCE_TTL_SECONDS = 120


class PresenceService:
    """Track online users and driver operational status."""

    def __init__(self, redis_client: Redis) -> None:
        self._redis = redis_client

    def _key(self, company_id: uuid.UUID) -> str:
        return f"presence:company:{company_id}"

    def mark_online(
        self,
        *,
        company_id: uuid.UUID,
        user_id: uuid.UUID,
        role: UserRole,
        status: str = "online",
        active_order_id: uuid.UUID | None = None,
    ) -> dict[str, Any]:
        """Mark a user online with optional active order."""
        payload = {
            "user_id": str(user_id),
            "role": role.value,
            "status": status,
            "active_order_id": str(active_order_id) if active_order_id else None,
            "last_seen": datetime.now(tz=UTC).isoformat(),
        }
        self._redis.hset(self._key(company_id), str(user_id), json.dumps(payload))
        self._redis.expire(self._key(company_id), PRESENCE_TTL_SECONDS * 10)
        return payload

    def touch(
        self,
        *,
        company_id: uuid.UUID,
        user_id: uuid.UUID,
        status: str | None = None,
    ) -> None:
        """Refresh last seen for a user."""
        raw = self._redis.hget(self._key(company_id), str(user_id))
        if raw is None:
            return
        payload = json.loads(raw)
        payload["last_seen"] = datetime.now(tz=UTC).isoformat()
        if status is not None:
            payload["status"] = status
        self._redis.hset(self._key(company_id), str(user_id), json.dumps(payload))

    def mark_offline(self, *, company_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """Remove a user from presence."""
        self._redis.hdel(self._key(company_id), str(user_id))

    def list_company_presence(self, company_id: uuid.UUID) -> list[dict[str, Any]]:
        """Return all presence records for a company."""
        records = self._redis.hgetall(self._key(company_id))
        result: list[dict[str, Any]] = []
        now = datetime.now(tz=UTC)
        for raw in records.values():
            payload = json.loads(raw)
            last_seen = datetime.fromisoformat(payload["last_seen"])
            if (now - last_seen).total_seconds() > PRESENCE_TTL_SECONDS:
                continue
            result.append(payload)
        return result

    def count_online(
        self,
        company_id: uuid.UUID,
        *,
        role: UserRole | None = None,
    ) -> int:
        """Count online users, optionally filtered by role."""
        records = self.list_company_presence(company_id)
        if role is None:
            return len(records)
        return sum(1 for item in records if item.get("role") == role.value)
