"""Trailer API schemas."""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class TrailerResponse(BaseModel):
    """Trailer response payload."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    registration_number: str
    manufacturer: str | None
    model: str | None
    trailer_type: str | None
    maximum_height: Decimal | None
    maximum_weight: Decimal | None
    maximum_vehicle_count: int
    active: bool
    created_at: datetime
    updated_at: datetime


class TrailerCreateRequest(BaseModel):
    """Create trailer payload."""

    registration_number: str = Field(min_length=1, max_length=32)
    manufacturer: str | None = Field(default=None, max_length=100)
    model: str | None = Field(default=None, max_length=100)
    trailer_type: str | None = Field(default=None, max_length=100)
    maximum_height: Decimal | None = Field(default=None, ge=0)
    maximum_weight: Decimal | None = Field(default=None, ge=0)
    maximum_vehicle_count: int = Field(ge=1, le=10)
    active: bool = True


class TrailerUpdateRequest(BaseModel):
    """Update trailer payload."""

    registration_number: str = Field(min_length=1, max_length=32)
    manufacturer: str | None = Field(default=None, max_length=100)
    model: str | None = Field(default=None, max_length=100)
    trailer_type: str | None = Field(default=None, max_length=100)
    maximum_height: Decimal | None = Field(default=None, ge=0)
    maximum_weight: Decimal | None = Field(default=None, ge=0)
    maximum_vehicle_count: int = Field(ge=1, le=10)
    active: bool = True
