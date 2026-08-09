"""Order vehicle API schemas."""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class OrderVehicleResponse(BaseModel):
    """Order vehicle response payload."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    order_id: uuid.UUID
    pickup_stop_id: uuid.UUID | None
    delivery_stop_id: uuid.UUID | None
    vin: str | None
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
