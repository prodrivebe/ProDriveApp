"""Shared API schemas."""

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response payload."""

    status: str = Field(examples=["healthy"])
    service: str = Field(examples=["ProDrive API"])
    version: str = Field(examples=["0.1.0"])


class ReadinessResponse(BaseModel):
    """Readiness probe with dependency checks."""

    status: str = Field(examples=["ready"])
    service: str
    version: str
    checks: dict[str, str]
