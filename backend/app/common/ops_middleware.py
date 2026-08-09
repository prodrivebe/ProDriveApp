"""Production middleware for pilot deployments."""

from __future__ import annotations

import logging
import time
from collections import defaultdict, deque
from typing import Final

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.config.settings import Settings

logger = logging.getLogger(__name__)

_HEALTH_PREFIXES: Final[tuple[str, ...]] = (
    "/api/v1/health",
    "/docs",
    "/redoc",
    "/openapi.json",
)
_AUTH_PATHS: Final[frozenset[str]] = frozenset(
    {
        "/api/v1/auth/login",
        "/api/v1/auth/refresh",
        "/api/v1/auth/password-reset/request",
        "/api/v1/auth/password-reset/confirm",
    }
)
_FEATURE_PATH_PREFIXES: Final[dict[str, tuple[str, ...]]] = {
    "ai": ("/api/v1/ai",),
    "planning": ("/api/v1/planning",),
    "realtime": ("/api/v1/realtime", "/api/v1/ws"),
}


class MaintenanceModeMiddleware(BaseHTTPMiddleware):
    """Return 503 for application traffic while maintenance mode is enabled."""

    def __init__(self, app, settings: Settings) -> None:
        super().__init__(app)
        self._settings = settings

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if not self._settings.maintenance_mode:
            return await call_next(request)

        path = request.url.path
        if any(path.startswith(prefix) for prefix in _HEALTH_PREFIXES):
            return await call_next(request)

        return JSONResponse(
            status_code=503,
            content={
                "success": False,
                "error": {
                    "code": "MAINTENANCE_MODE",
                    "message": self._settings.maintenance_message,
                },
            },
            headers={"Retry-After": "300"},
        )


class FeatureFlagMiddleware(BaseHTTPMiddleware):
    """Block disabled feature modules at the edge."""

    def __init__(self, app, settings: Settings) -> None:
        super().__init__(app)
        self._settings = settings

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        path = request.url.path
        for feature_name, prefixes in _FEATURE_PATH_PREFIXES.items():
            if not self._settings.is_feature_enabled(feature_name):
                if any(path.startswith(prefix) for prefix in prefixes):
                    return JSONResponse(
                        status_code=503,
                        content={
                            "success": False,
                            "error": {
                                "code": "FEATURE_DISABLED",
                                "message": f"The {feature_name} feature is disabled.",
                            },
                        },
                    )
        return await call_next(request)


class AuthRateLimitMiddleware(BaseHTTPMiddleware):
    """Limit authentication endpoint abuse by client IP."""

    def __init__(self, app, settings: Settings) -> None:
        super().__init__(app)
        self._settings = settings
        self._requests: dict[str, deque[float]] = defaultdict(deque)

    def _client_ip(self, request: Request) -> str:
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        if request.client is not None:
            return request.client.host
        return "unknown"

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.url.path not in _AUTH_PATHS:
            return await call_next(request)

        if self._settings.auth_rate_limit_per_minute <= 0:
            return await call_next(request)

        client_ip = self._client_ip(request)
        now = time.time()
        window_start = now - 60
        bucket = self._requests[client_ip]
        while bucket and bucket[0] < window_start:
            bucket.popleft()

        if len(bucket) >= self._settings.auth_rate_limit_per_minute:
            logger.warning("Auth rate limit exceeded for ip=%s path=%s", client_ip, request.url.path)
            return JSONResponse(
                status_code=429,
                content={
                    "success": False,
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": "Too many authentication attempts. Try again later.",
                    },
                },
                headers={"Retry-After": "60"},
            )

        bucket.append(now)
        return await call_next(request)


def build_ops_status(settings: Settings) -> dict[str, object]:
    """Return non-sensitive operational status for monitoring."""
    return {
        "maintenance_mode": settings.maintenance_mode,
        "feature_flags": settings.feature_flags,
        "environment": settings.environment,
    }
