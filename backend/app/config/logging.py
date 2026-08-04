"""Central logging configuration."""

import json
import logging
import logging.config
from datetime import UTC, datetime
from typing import Any

from app.config.settings import Settings


class JsonFormatter(logging.Formatter):
    """Format log records as structured JSON."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=True)


def configure_logging(settings: Settings) -> None:
    """Configure application-wide logging."""
    formatter_name = "json" if settings.log_json else "plain"
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "json": {
                    "()": JsonFormatter,
                },
                "plain": {
                    "format": "%(asctime)s %(levelname)s [%(name)s] %(message)s",
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": formatter_name,
                },
            },
            "root": {
                "level": settings.log_level.upper(),
                "handlers": ["console"],
            },
            "loggers": {
                "uvicorn": {
                    "level": settings.log_level.upper(),
                    "handlers": ["console"],
                    "propagate": False,
                },
                "uvicorn.error": {
                    "level": settings.log_level.upper(),
                    "handlers": ["console"],
                    "propagate": False,
                },
                "uvicorn.access": {
                    "level": settings.log_level.upper(),
                    "handlers": ["console"],
                    "propagate": False,
                },
            },
        }
    )
