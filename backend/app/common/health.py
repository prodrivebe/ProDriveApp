"""Readiness and dependency health checks."""

from __future__ import annotations

import logging

from redis import Redis
from sqlalchemy import text

from app.config.settings import Settings
from app.database.session import get_engine

logger = logging.getLogger(__name__)


def check_database() -> tuple[bool, str]:
    """Verify database connectivity."""
    try:
        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1"))
        return True, "ok"
    except Exception as exc:
        logger.warning("Database readiness check failed: %s", exc)
        return False, "unavailable"


def check_redis(settings: Settings) -> tuple[bool, str]:
    """Verify Redis connectivity."""
    if settings.environment == "test":
        return True, "skipped"
    client: Redis | None = None
    try:
        client = Redis.from_url(settings.redis_url, decode_responses=True)
        client.ping()
        return True, "ok"
    except Exception as exc:
        logger.warning("Redis readiness check failed: %s", exc)
        return False, "unavailable"
    finally:
        if client is not None:
            client.close()
