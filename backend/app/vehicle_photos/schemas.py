"""Vehicle photo API schemas."""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.common.enums import PhotoType


class VehiclePhotoResponse(BaseModel):
    """Vehicle photo response payload."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    order_id: uuid.UUID | None
    vehicle_id: uuid.UUID
    photo_type: PhotoType
    file_path: str
    file_name: str | None
    file_size: int | None
    content_type: str | None
    metadata_json: str | None = None
    uploaded_by: uuid.UUID | None
    uploaded_at: datetime
    gps_latitude: Decimal | None
    gps_longitude: Decimal | None
