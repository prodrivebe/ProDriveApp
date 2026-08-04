"""Shared API routes."""

from fastapi import APIRouter, Depends

from app.common.schemas import HealthResponse
from app.config.settings import Settings, get_settings

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
def health_check(settings: Settings = Depends(get_settings)) -> HealthResponse:
    """Return service health status."""
    return HealthResponse(
        status="healthy",
        service=settings.app_name,
        version=settings.app_version,
    )
