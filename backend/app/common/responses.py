"""Standard API response helpers."""

from typing import Any

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Structured API error payload."""

    code: str
    message: str


class ErrorResponse(BaseModel):
    """Standard error response envelope."""

    success: bool = False
    error: ErrorDetail


class SuccessResponse[T](BaseModel):
    """Standard success response envelope."""

    success: bool = True
    data: T
    meta: dict[str, Any] = Field(default_factory=dict)


def success_response[T](
    data: T,
    meta: dict[str, Any] | None = None,
) -> SuccessResponse[T]:
    """Build a standard success response."""
    return SuccessResponse(data=data, meta=meta or {})
