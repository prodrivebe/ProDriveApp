"""Shared API routes."""

import logging

from fastapi import APIRouter, Depends, Response, status
from fastapi.responses import JSONResponse

from app.common.health import check_database, check_redis
from app.common.ops_middleware import build_ops_status
from app.common.schemas import HealthResponse, OpsStatusResponse, ReadinessResponse
from app.config.settings import Settings, get_settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
def health_check(settings: Settings = Depends(get_settings)) -> HealthResponse:
    """Return service liveness status."""
    return HealthResponse(
        status="healthy",
        service=settings.app_name,
        version=settings.app_version,
    )


@router.get("/health/ready", response_model=ReadinessResponse)
def readiness_check(settings: Settings = Depends(get_settings)) -> Response:
    """Return readiness based on database and Redis availability."""
    db_ok, db_status = check_database()
    redis_ok, redis_status = check_redis(settings)
    checks = {"database": db_status, "redis": redis_status}
    ready = db_ok and redis_ok
    payload = ReadinessResponse(
        status="ready" if ready else "degraded",
        service=settings.app_name,
        version=settings.app_version,
        checks=checks,
    )
    return JSONResponse(
        status_code=status.HTTP_200_OK if ready else status.HTTP_503_SERVICE_UNAVAILABLE,
        content=payload.model_dump(),
    )


@router.get("/health/ops", response_model=OpsStatusResponse)
def ops_status(settings: Settings = Depends(get_settings)) -> OpsStatusResponse:
    """Return operational status for monitoring dashboards."""
    ops = build_ops_status(settings)
    return OpsStatusResponse(
        status="ok",
        service=settings.app_name,
        version=settings.app_version,
        maintenance_mode=bool(ops["maintenance_mode"]),
        feature_flags=dict(ops["feature_flags"]),
        environment=str(ops["environment"]),
    )
