"""Planning API schemas."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class PlanningBoardQuery(BaseModel):
    """Planning board filters."""

    search: str | None = None
    planned_date: date | None = None
    driver_id: uuid.UUID | None = None
    truck_id: uuid.UUID | None = None
    trailer_id: uuid.UUID | None = None


class PlanningOrderCard(BaseModel):
    """Order summary for planning board."""

    id: uuid.UUID
    order_number: str
    status: str
    customer_id: uuid.UUID
    assigned_driver_id: uuid.UUID | None
    assigned_truck_id: uuid.UUID | None
    assigned_trailer_id: uuid.UUID | None
    planned_pickup_date: date | None
    planned_delivery_date: date | None
    vehicle_count: int
    column: str


class ResourceAvailability(BaseModel):
    """Fleet resource availability indicator."""

    id: uuid.UUID
    label: str
    resource_type: str
    available: bool
    active_assignments: int
    capacity_indicator: str | None = None
    conflict: bool = False
    conflict_reason: str | None = None


class PlanningBoardResponse(BaseModel):
    """Planning board payload."""

    columns: dict[str, list[PlanningOrderCard]]
    drivers: list[ResourceAvailability]
    trucks: list[ResourceAvailability]
    trailers: list[ResourceAvailability]
    active_assignments: list[dict[str, object]]


class PlanningAssignRequest(BaseModel):
    """Assign or reassign fleet resources to an order."""

    order_id: uuid.UUID
    driver_id: uuid.UUID | None = None
    truck_id: uuid.UUID | None = None
    trailer_id: uuid.UUID | None = None
    clear_assignment: bool = False


class LoadingPositionInput(BaseModel):
    """Manual or recommended loading position."""

    vehicle_id: uuid.UUID
    upper_deck: bool = False
    trailer_position: int = Field(ge=1)
    loading_order: int = Field(ge=1)
    unloading_order: int = Field(ge=1)
    destination_city: str | None = None


class LoadPlanRequest(BaseModel):
    """Create or update a loading plan draft."""

    order_id: uuid.UUID
    positions: list[LoadingPositionInput] = Field(default_factory=list)
    route_sequence: list[uuid.UUID] | None = None
    confirm: bool = False
    suggestion_id: uuid.UUID | None = None
    acknowledge_warnings: bool = False


class OptimizeRequest(BaseModel):
    """Request loading/route optimization."""

    order_id: uuid.UUID
    include_route: bool = True


class ValidateRequest(BaseModel):
    """Validate loading plan or draft positions."""

    order_id: uuid.UUID
    positions: list[LoadingPositionInput] = Field(default_factory=list)
    route_sequence: list[uuid.UUID] | None = None


class LoadingPositionResponse(BaseModel):
    """Persisted loading position."""

    vehicle_id: uuid.UUID
    vehicle_label: str | None = None
    upper_deck: bool
    trailer_position: int
    loading_order: int
    unloading_order: int
    destination_city: str | None = None
    weight_kg: float | None = None
    height_m: float | None = None
    confirmed_by_dispatcher: bool = False
    ai_generated: bool = False


class LoadPlanResponse(BaseModel):
    """Loading plan response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    order_id: uuid.UUID
    trailer_id: uuid.UUID | None
    status: str
    estimated_total_height: float | None
    estimated_total_weight: float | None
    estimated_travel_km: float | None
    front_axle_percent: float | None
    rear_axle_percent: float | None
    warnings: list[str] = Field(default_factory=list)
    positions: list[LoadingPositionResponse] = Field(default_factory=list)
    route_sequence: list[uuid.UUID] = Field(default_factory=list)
    created_at: datetime
    confirmed_at: datetime | None = None


class OptimizationResponse(BaseModel):
    """Optimization recommendation awaiting approval."""

    suggestion_id: uuid.UUID
    order_id: uuid.UUID
    loading: dict[str, object]
    route: dict[str, object] | None = None
    validation: dict[str, object]
    confidence: float
    reasoning: list[str]
    status: str


class ValidationResponse(BaseModel):
    """Validation result."""

    is_valid: bool
    errors: list[dict[str, object]]
    warnings: list[dict[str, object]]
    estimated_total_height_m: float
    estimated_total_weight_kg: float
    front_axle_percent: float
    rear_axle_percent: float
