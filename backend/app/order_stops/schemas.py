"""Order stop API schemas."""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.common.enums import StopProgressStatus, StopType


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
