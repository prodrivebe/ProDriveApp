"""Order document API schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.common.enums import OrderDocumentType

from app.order_stops.schemas import OrderStopResponse
from app.orders.schemas import OrderResponse


class OrderDocumentResponse(BaseModel):
    """Order document response payload."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    order_id: uuid.UUID
    document_type: OrderDocumentType
    file_path: str
    file_name: str
    version: int
    is_locked: bool
    uploaded_by: uuid.UUID | None
    uploaded_at: datetime


class OrderDocumentUploadResponse(BaseModel):
    """Document upload payload including updated workflow context."""

    document: OrderDocumentResponse
    order: OrderResponse
    stop: OrderStopResponse | None = None


class CmrSignRequest(BaseModel):
    """Driver signature payload for CMR finalization."""

    signature_png_base64: str = Field(min_length=32)


class CmrSignResponse(BaseModel):
    """Signed and locked CMR with updated workflow context."""

    document: OrderDocumentResponse
    order: OrderResponse
    stop: OrderStopResponse | None = None
