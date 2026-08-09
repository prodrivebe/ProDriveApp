"""Vehicle damage API schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.common.enums import DamageSeverity, DamageType


class VehicleDamageResponse(BaseModel):
    """Vehicle damage response payload."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    order_id: uuid.UUID
    vehicle_id: uuid.UUID
    damage_type: DamageType
    severity: DamageSeverity
    description: str | None
    location: str | None
    reported_by: uuid.UUID | None
    reported_at: datetime
    photo_ids: list[uuid.UUID] = []


class VehicleDamageCreateRequest(BaseModel):
    """Create vehicle damage payload."""

    damage_type: DamageType
    severity: DamageSeverity
    description: str | None = Field(default=None, max_length=5000)
    location: str | None = Field(default=None, max_length=255)
    photo_ids: list[uuid.UUID] = Field(default_factory=list)


class VehicleDamageUpdateRequest(BaseModel):
    """Update vehicle damage payload."""

    damage_type: DamageType
    severity: DamageSeverity
    description: str | None = Field(default=None, max_length=5000)
    location: str | None = Field(default=None, max_length=255)
    photo_ids: list[uuid.UUID] = Field(default_factory=list)
