"""Order timeline API schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class OrderTimelineResponse(BaseModel):
    """Order timeline entry response payload."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    order_id: uuid.UUID
    event_type: str
    description: str
    created_by: uuid.UUID | None
    created_at: datetime
