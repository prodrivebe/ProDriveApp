"""Truck operational record API schemas."""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class TruckMaintenanceRecordResponse(BaseModel):
    """Truck maintenance record response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    truck_id: uuid.UUID
    maintenance_date: date
    mileage: int | None
    maintenance_type: str
    notes: str | None
    created_at: datetime
    updated_at: datetime


class TruckMaintenanceRecordCreateRequest(BaseModel):
    """Create truck maintenance record payload."""

    maintenance_date: date
    mileage: int | None = Field(default=None, ge=0)
    maintenance_type: str = Field(min_length=1, max_length=100)
    notes: str | None = Field(default=None, max_length=5000)


class TruckMaintenanceRecordUpdateRequest(TruckMaintenanceRecordCreateRequest):
    """Update truck maintenance record payload."""


class TruckInspectionRecordResponse(BaseModel):
    """Truck inspection record response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    truck_id: uuid.UUID
    inspection_date: date
    mileage: int | None
    inspection_type: str
    notes: str | None
    created_at: datetime
    updated_at: datetime


class TruckInspectionRecordCreateRequest(BaseModel):
    """Create truck inspection record payload."""

    inspection_date: date
    mileage: int | None = Field(default=None, ge=0)
    inspection_type: str = Field(min_length=1, max_length=100)
    notes: str | None = Field(default=None, max_length=5000)


class TruckInspectionRecordUpdateRequest(TruckInspectionRecordCreateRequest):
    """Update truck inspection record payload."""


class TruckTireRecordResponse(BaseModel):
    """Truck tire record response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    truck_id: uuid.UUID
    tire_date: date
    mileage: int | None
    tire_type: str
    notes: str | None
    created_at: datetime
    updated_at: datetime


class TruckTireRecordCreateRequest(BaseModel):
    """Create truck tire record payload."""

    tire_date: date
    mileage: int | None = Field(default=None, ge=0)
    tire_type: str = Field(min_length=1, max_length=100)
    notes: str | None = Field(default=None, max_length=5000)


class TruckTireRecordUpdateRequest(TruckTireRecordCreateRequest):
    """Update truck tire record payload."""
