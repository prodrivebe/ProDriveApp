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
    vehicle_id: uuid.UUID
    file_path: str
    photo_type: PhotoType
    uploaded_by: uuid.UUID | None
    uploaded_at: datetime
    gps_latitude: Decimal | None
    gps_longitude: Decimal | None


class VehiclePhotoUploadRequest(BaseModel):
    """Optional metadata for a vehicle photo upload."""

    photo_type: PhotoType = PhotoType.CUSTOM
    gps_latitude: Decimal | None = None
    gps_longitude: Decimal | None = None
