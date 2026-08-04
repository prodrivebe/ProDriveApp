"""Redis client infrastructure (prepared for future use)."""

from redis import Redis

from app.config.settings import Settings


class RedisClient:
    """Lazy Redis client wrapper."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client: Redis | None = None

    @property
    def client(self) -> Redis:
        """Return an initialized Redis client."""
        if self._client is None:
            self._client = Redis.from_url(
                self._settings.redis_url,
                decode_responses=True,
            )
        return self._client

    def close(self) -> None:
        """Close the Redis connection."""
        if self._client is not None:
            self._client.close()
            self._client = None


def get_redis_client(settings: Settings) -> RedisClient:
    """Create a Redis client wrapper."""
    return RedisClient(settings)
