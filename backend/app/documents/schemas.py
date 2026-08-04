"""Document API schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.common.enums import DocumentType


class DocumentResponse(BaseModel):
    """Document response payload."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    order_id: uuid.UUID
    document_type: DocumentType
    file_path: str
    generated_at: datetime
    generated_by: uuid.UUID | None
