"""Fleet overview schemas."""

from pydantic import BaseModel


class FleetEntitySummary(BaseModel):
    """Summary counts for a fleet entity type."""

    total: int
    active: int


class FleetOverviewResponse(BaseModel):
    """Fleet overview response payload."""

    drivers: FleetEntitySummary
    trucks: FleetEntitySummary
    trailers: FleetEntitySummary
