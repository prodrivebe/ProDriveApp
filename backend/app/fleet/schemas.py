"""Fleet schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class FleetEntitySummary(BaseModel):
    """Summary counts for a fleet entity type."""

    total: int
    active: int


class FleetOverviewResponse(BaseModel):
    """Fleet overview response payload."""

    drivers: FleetEntitySummary
    trucks: FleetEntitySummary
    trailers: FleetEntitySummary


class FleetAssignmentCreateRequest(BaseModel):
    """Payload for creating a fleet assignment."""

    driver_id: uuid.UUID
    truck_id: uuid.UUID
    trailer_id: uuid.UUID


class FleetAssignmentResponse(BaseModel):
    """Fleet assignment response payload."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    driver_id: uuid.UUID
    truck_id: uuid.UUID
    trailer_id: uuid.UUID
    assigned_at: datetime
    unassigned_at: datetime | None
    active: bool
