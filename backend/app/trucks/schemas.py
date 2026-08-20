"""Truck API schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TruckResponse(BaseModel):
    """Truck response payload."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    registration_number: str
    brand: str | None
    model: str | None
    vin: str | None
    capacity: int | None
    current_mileage: int | None
    active: bool
    created_at: datetime
    updated_at: datetime


class TruckCreateRequest(BaseModel):
    """Create truck payload."""

    registration_number: str = Field(min_length=1, max_length=32)
    brand: str | None = Field(default=None, max_length=100)
    model: str | None = Field(default=None, max_length=100)
    vin: str | None = Field(default=None, max_length=32)
    capacity: int | None = Field(default=None, ge=1)
    current_mileage: int | None = Field(default=None, ge=0)
    active: bool = True


class TruckUpdateRequest(BaseModel):
    """Update truck payload."""

    registration_number: str = Field(min_length=1, max_length=32)
    brand: str | None = Field(default=None, max_length=100)
    model: str | None = Field(default=None, max_length=100)
    vin: str | None = Field(default=None, max_length=32)
    capacity: int | None = Field(default=None, ge=1)
    current_mileage: int | None = Field(default=None, ge=0)
    active: bool = True
