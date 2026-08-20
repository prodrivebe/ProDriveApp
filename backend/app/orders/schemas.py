"""Order API schemas."""

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.common.enums import OrderStatus, StopProgressStatus, StopType
from app.orders.validators import MAX_ORDER_VEHICLES, is_loading_locked


class OrderStopResponse(BaseModel):
    """Order stop response payload."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    order_id: uuid.UUID
    stop_type: StopType
    sequence: int
    company_name: str | None
    contact_name: str | None
    phone: str | None
    address: str | None
    city: str | None
    postal_code: str | None
    country: str | None
    latitude: Decimal | None
    longitude: Decimal | None
    arrival_time: datetime | None
    departure_time: datetime | None
    progress_status: StopProgressStatus
    created_at: datetime
    updated_at: datetime


class OrderStopCreateRequest(BaseModel):
    """Create order stop payload."""

    stop_type: StopType
    sequence: int = Field(ge=1)
    company_name: str | None = Field(default=None, max_length=255)
    contact_name: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=50)
    address: str | None = Field(default=None, max_length=500)
    city: str | None = Field(default=None, max_length=100)
    postal_code: str | None = Field(default=None, max_length=20)
    country: str | None = Field(default=None, max_length=100)
    latitude: Decimal | None = None
    longitude: Decimal | None = None


class OrderStopUpdateRequest(OrderStopCreateRequest):
    """Update order stop payload."""


class OrderVehicleResponse(BaseModel):
    """Order vehicle response payload."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    order_id: uuid.UUID
    pickup_stop_id: uuid.UUID | None
    delivery_stop_id: uuid.UUID | None
    vin: str | None
    verified_vin: str | None
    make: str | None
    model: str | None
    generation: str | None
    body_type: str | None
    color: str | None
    year: int | None
    fuel_type: str | None
    transmission: str | None
    running: bool | None
    estimated_weight: Decimal | None
    estimated_height: Decimal | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


class OrderVehicleCreateRequest(BaseModel):
    """Create order vehicle payload."""

    pickup_stop_id: uuid.UUID | None = None
    delivery_stop_id: uuid.UUID | None = None
    vin: str | None = Field(default=None, max_length=17)
    make: str | None = Field(default=None, max_length=100)
    model: str | None = Field(default=None, max_length=100)
    generation: str | None = Field(default=None, max_length=100)
    body_type: str | None = Field(default=None, max_length=100)
    color: str | None = Field(default=None, max_length=50)
    year: int | None = Field(default=None, ge=1900, le=2100)
    fuel_type: str | None = Field(default=None, max_length=50)
    transmission: str | None = Field(default=None, max_length=50)
    running: bool | None = None
    estimated_weight: Decimal | None = Field(default=None, ge=0)
    estimated_height: Decimal | None = Field(default=None, ge=0)
    notes: str | None = Field(default=None, max_length=5000)


class OrderVehicleUpdateRequest(OrderVehicleCreateRequest):
    """Update order vehicle payload."""


class VinUpdateRequest(BaseModel):
    """VIN scan or update payload."""

    vin: str = Field(min_length=1, max_length=17)


class OrderResponse(BaseModel):
    """Detailed order response payload."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    customer_id: uuid.UUID
    order_number: str
    status: OrderStatus
    assigned_driver_id: uuid.UUID | None
    assigned_truck_id: uuid.UUID | None
    assigned_trailer_id: uuid.UUID | None
    planned_pickup_date: date | None
    planned_delivery_date: date | None
    customer_reference_numbers: list[str] = Field(default_factory=list)
    notes: str | None
    created_at: datetime
    updated_at: datetime
    customer_name: str | None = None
    assigned_driver_name: str | None = None
    stops: list[OrderStopResponse] = Field(default_factory=list)
    vehicles: list[OrderVehicleResponse] = Field(default_factory=list)

    @computed_field
    @property
    def loading_locked(self) -> bool:
        """Whether vehicle editing is locked after loading completed."""
        return is_loading_locked(self.status)


class ReopenLoadingRequest(BaseModel):
    """Dispatcher request to reopen loading on a loaded order."""

    reason: str = Field(default="", max_length=2000)


class OrderListResponse(BaseModel):
    """Compact order response for list views."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    customer_id: uuid.UUID
    order_number: str
    status: OrderStatus
    assigned_driver_id: uuid.UUID | None
    assigned_truck_id: uuid.UUID | None
    assigned_trailer_id: uuid.UUID | None
    planned_pickup_date: date | None
    planned_delivery_date: date | None
    customer_reference_numbers: list[str] = Field(default_factory=list)
    notes: str | None
    created_at: datetime
    updated_at: datetime
    customer_name: str | None = None
    assigned_driver_name: str | None = None


class OrderCreateRequest(BaseModel):
    """Create order payload for the order wizard."""

    customer_id: uuid.UUID
    planned_pickup_date: date | None = None
    planned_delivery_date: date | None = None
    customer_reference_numbers: list[str] = Field(default_factory=list, max_length=20)
    notes: str | None = Field(default=None, max_length=5000)
    stops: list[OrderStopCreateRequest] = Field(default_factory=list)
    vehicles: list[OrderVehicleCreateRequest] = Field(default_factory=list, max_length=MAX_ORDER_VEHICLES)


class OrderUpdateRequest(BaseModel):
    """Update order payload."""

    customer_id: uuid.UUID
    planned_pickup_date: date | None = None
    planned_delivery_date: date | None = None
    customer_reference_numbers: list[str] | None = Field(default=None, max_length=20)
    notes: str | None = Field(default=None, max_length=5000)
    status: OrderStatus | None = None


class AssignDriverRequest(BaseModel):
    """Assign fleet resources to an order."""

    driver_id: uuid.UUID
    truck_id: uuid.UUID | None = None
    trailer_id: uuid.UUID | None = None


class OrderTimelineResponse(BaseModel):
    """Order timeline entry response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    order_id: uuid.UUID
    event_type: str
    description: str
    created_by: uuid.UUID | None
    created_at: datetime


class OrderSummaryResponse(BaseModel):
    """Compact order response for list and history views."""

    id: uuid.UUID
    order_number: str
    status: OrderStatus
    customer_id: uuid.UUID
    planned_pickup_date: date | None
    planned_delivery_date: date | None
    created_at: datetime
