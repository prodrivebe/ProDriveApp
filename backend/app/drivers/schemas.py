"""Driver API schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.orders.schemas import OrderSummaryResponse


class DriverResponse(BaseModel):
    """Driver profile response payload."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    user_id: uuid.UUID
    phone: str | None
    driving_license: str | None
    adr_certificate: str | None
    notes: str | None
    active: bool
    created_at: datetime
    updated_at: datetime


class DriverCreateRequest(BaseModel):
    """Create driver profile payload."""

    user_id: uuid.UUID
    phone: str | None = Field(default=None, max_length=50)
    driving_license: str | None = Field(default=None, max_length=100)
    adr_certificate: str | None = Field(default=None, max_length=100)
    notes: str | None = Field(default=None, max_length=1000)
    active: bool = True


class DriverUpdateRequest(BaseModel):
    """Update driver profile payload."""

    phone: str | None = Field(default=None, max_length=50)
    driving_license: str | None = Field(default=None, max_length=100)
    adr_certificate: str | None = Field(default=None, max_length=100)
    notes: str | None = Field(default=None, max_length=1000)
    active: bool = True


class DriverHomeResponse(BaseModel):
    """Driver home screen payload."""

    driver: DriverResponse
    user_name: str
    truck_label: str | None = None
    trailer_label: str | None = None
    current_order: OrderSummaryResponse | None = None
    next_action: str
    unread_notifications: int = 0
