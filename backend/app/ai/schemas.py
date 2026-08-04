"""AI API schemas."""

import uuid
from datetime import date

from pydantic import BaseModel, Field

from app.common.enums import StopType
from app.orders.schemas import OrderStopCreateRequest, OrderVehicleCreateRequest


class ParseOrderRequest(BaseModel):
    """Parse unstructured customer message."""

    message: str = Field(min_length=1, max_length=10000)


class ParsedOrderDraft(BaseModel):
    """Structured draft extracted from a customer message."""

    pickup_stops: list[OrderStopCreateRequest] = Field(default_factory=list)
    delivery_stops: list[OrderStopCreateRequest] = Field(default_factory=list)
    vehicles: list[OrderVehicleCreateRequest] = Field(default_factory=list)
    planned_pickup_date: date | None = None
    planned_delivery_date: date | None = None
    missing_fields: list[str] = Field(default_factory=list)
    confidence_score: float = Field(ge=0, le=1)


class OrderScopedRequest(BaseModel):
    """Order-scoped AI request."""

    order_id: uuid.UUID


class DriverSuggestion(BaseModel):
    """Suggested driver candidate."""

    driver_id: uuid.UUID
    driver_name: str
    score: float = Field(ge=0, le=1)
    reason: str


class SuggestDriverResponse(BaseModel):
    """Driver recommendation response."""

    recommended: DriverSuggestion | None
    alternatives: list[DriverSuggestion] = Field(default_factory=list)


class RouteStopSuggestion(BaseModel):
    """Suggested stop order."""

    stop_id: uuid.UUID
    sequence: int
    stop_type: StopType


class SuggestRouteResponse(BaseModel):
    """Route optimization suggestion."""

    stops: list[RouteStopSuggestion]
    confidence_score: float = Field(ge=0, le=1)


class LoadingPositionSuggestion(BaseModel):
    """Suggested loading position for a vehicle."""

    vehicle_id: uuid.UUID
    loading_order: int
    trailer_position: int


class SuggestLoadingResponse(BaseModel):
    """Trailer loading suggestion."""

    positions: list[LoadingPositionSuggestion]
    confidence_score: float = Field(ge=0, le=1)


class OrderQualityResponse(BaseModel):
    """Order completeness and quality score."""

    score: float = Field(ge=0, le=1)
    missing_fields: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class EmptyKmSuggestion(BaseModel):
    """Suggested use of empty kilometers."""

    driver_id: uuid.UUID | None = None
    driver_name: str | None = None
    suggested_route: str
    estimated_empty_km: float = Field(ge=0)
    reason: str


class SuggestEmptyKmResponse(BaseModel):
    """Empty kilometer optimization suggestions."""

    suggestions: list[EmptyKmSuggestion] = Field(default_factory=list)
    confidence_score: float = Field(ge=0, le=1)
