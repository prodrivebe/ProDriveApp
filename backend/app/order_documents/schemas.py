"""Order document API schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.common.enums import OrderDocumentType


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
    uploaded_by: uuid.UUID | None
    uploaded_at: datetime
