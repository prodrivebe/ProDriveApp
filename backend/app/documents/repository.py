"""Document persistence layer."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.enums import DocumentType
from app.documents.models import Document


class DocumentRepository:
    """Repository for document records."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def get_latest_for_order(
        self,
        order_id: uuid.UUID,
        company_id: uuid.UUID,
        document_type: DocumentType,
    ) -> Document | None:
        """Return the latest document of a type for an order."""
        statement = (
            select(Document)
            .where(
                Document.order_id == order_id,
                Document.company_id == company_id,
                Document.document_type == document_type,
            )
            .order_by(Document.generated_at.desc())
            .limit(1)
        )
        return self._db.scalar(statement)

    def list_for_order(
        self,
        order_id: uuid.UUID,
        company_id: uuid.UUID,
    ) -> list[Document]:
        """Return all documents for an order ordered newest first."""
        statement = (
            select(Document)
            .where(
                Document.order_id == order_id,
                Document.company_id == company_id,
            )
            .order_by(Document.generated_at.desc())
        )
        return list(self._db.scalars(statement).all())

    def create(
        self,
        *,
        company_id: uuid.UUID,
        order_id: uuid.UUID,
        document_type: DocumentType,
        file_path: str,
        generated_by: uuid.UUID,
    ) -> Document:
        """Create a document record."""
        document = Document(
            company_id=company_id,
            order_id=order_id,
            document_type=document_type,
            file_path=file_path,
            generated_at=datetime.now(tz=UTC),
            generated_by=generated_by,
        )
        self._db.add(document)
        self._db.commit()
        self._db.refresh(document)
        return document
