"""HTTP middleware for observability."""

from __future__ import annotations

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("prodrive.request")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log request duration and attach a correlation id."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        start = time.perf_counter()
        response: Response | None = None
        try:
            response = await call_next(request)
            return response
        finally:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            status_code = response.status_code if response is not None else 500
            logger.info(
                "request completed request_id=%s method=%s path=%s status=%s duration_ms=%s",
                request_id,
                request.method,
                request.url.path,
                status_code,
                duration_ms,
            )
            if response is not None:
                response.headers["X-Request-ID"] = request_id
