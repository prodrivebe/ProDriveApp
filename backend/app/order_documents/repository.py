"""Order document persistence layer."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.common.enums import OrderDocumentType
from app.order_documents.models import OrderDocument


class OrderDocumentRepository:
    """Repository for versioned order documents."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_id_for_company(
        self,
        document_id: uuid.UUID,
        company_id: uuid.UUID,
    ) -> OrderDocument | None:
        statement = select(OrderDocument).where(
            OrderDocument.id == document_id,
            OrderDocument.company_id == company_id,
            OrderDocument.deleted_at.is_(None),
        )
        return self._db.scalar(statement)

    def list_for_order(
        self,
        order_id: uuid.UUID,
        company_id: uuid.UUID,
    ) -> list[OrderDocument]:
        statement = (
            select(OrderDocument)
            .where(
                OrderDocument.order_id == order_id,
                OrderDocument.company_id == company_id,
                OrderDocument.deleted_at.is_(None),
            )
            .order_by(OrderDocument.uploaded_at.desc())
        )
        return list(self._db.scalars(statement).all())

    def get_latest_version(
        self,
        order_id: uuid.UUID,
        company_id: uuid.UUID,
        document_type: OrderDocumentType,
    ) -> int:
        latest = self._db.scalar(
            select(func.max(OrderDocument.version)).where(
                OrderDocument.order_id == order_id,
                OrderDocument.company_id == company_id,
                OrderDocument.document_type == document_type,
                OrderDocument.deleted_at.is_(None),
            )
        )
        return int(latest or 0)

    def create(
        self,
        *,
        company_id: uuid.UUID,
        order_id: uuid.UUID,
        document_type: OrderDocumentType,
        file_path: str,
        file_name: str,
        version: int,
        uploaded_by: uuid.UUID,
    ) -> OrderDocument:
        document = OrderDocument(
            company_id=company_id,
            order_id=order_id,
            document_type=document_type,
            file_path=file_path,
            file_name=file_name,
            version=version,
            uploaded_by=uploaded_by,
            uploaded_at=datetime.now(tz=UTC),
        )
        self._db.add(document)
        self._db.commit()
        self._db.refresh(document)
        return document

    def soft_delete(self, document: OrderDocument) -> OrderDocument:
        document.deleted_at = datetime.now(tz=UTC)
        self._db.add(document)
        self._db.commit()
        self._db.refresh(document)
        return document
