"""VIN verification API schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.common.enums import VinVerificationAction


class VinVerifyRequest(BaseModel):
    """Verify a vehicle VIN."""

    vin: str = Field(min_length=17, max_length=17)


class VinUpdateRequest(BaseModel):
    """Update a verified vehicle VIN."""

    vin: str = Field(min_length=17, max_length=17)


class VinHistoryResponse(BaseModel):
    """VIN verification history entry."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    order_id: uuid.UUID
    vehicle_id: uuid.UUID
    original_vin: str | None
    verified_vin: str
    action: VinVerificationAction
    verified_by: uuid.UUID | None
    verified_at: datetime


class VinVerificationResponse(BaseModel):
    """Current VIN verification state for a vehicle."""

    vehicle_id: uuid.UUID
    order_id: uuid.UUID
    vin: str | None
    original_vin: str | None
    verified_vin: str | None
    vin_verified_at: datetime | None
    vin_verified_by: uuid.UUID | None
