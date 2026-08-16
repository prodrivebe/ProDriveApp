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

    def has_signed_cmr_upload(
        self,
        order_id: uuid.UUID,
        company_id: uuid.UUID,
    ) -> bool:
        """Return whether a signed CMR copy (v2+) exists after pickup draft generation."""
        return (
            self.get_latest_version(order_id, company_id, OrderDocumentType.CMR) >= 2
        )

    def has_document(
        self,
        order_id: uuid.UUID,
        company_id: uuid.UUID,
        document_type: OrderDocumentType,
    ) -> bool:
        count = self._db.scalar(
            select(func.count())
            .select_from(OrderDocument)
            .where(
                OrderDocument.order_id == order_id,
                OrderDocument.company_id == company_id,
                OrderDocument.document_type == document_type,
                OrderDocument.deleted_at.is_(None),
            )
        )
        return int(count or 0) > 0

    def has_locked_document(
        self,
        order_id: uuid.UUID,
        company_id: uuid.UUID,
        document_type: OrderDocumentType,
    ) -> bool:
        locked = self._db.scalar(
            select(func.count())
            .select_from(OrderDocument)
            .where(
                OrderDocument.order_id == order_id,
                OrderDocument.company_id == company_id,
                OrderDocument.document_type == document_type,
                OrderDocument.is_locked.is_(True),
                OrderDocument.deleted_at.is_(None),
            )
        )
        return int(locked or 0) > 0

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
        is_locked: bool = False,
    ) -> OrderDocument:
        document = OrderDocument(
            company_id=company_id,
            order_id=order_id,
            document_type=document_type,
            file_path=file_path,
            file_name=file_name,
            version=version,
            is_locked=is_locked,
            uploaded_by=uploaded_by,
            uploaded_at=datetime.now(tz=UTC),
        )
        self._db.add(document)
        self._db.commit()
        self._db.refresh(document)
        return document

    def get_latest_document(
        self,
        order_id: uuid.UUID,
        company_id: uuid.UUID,
        document_type: OrderDocumentType,
        *,
        locked_only: bool = False,
    ) -> OrderDocument | None:
        filters = [
            OrderDocument.order_id == order_id,
            OrderDocument.company_id == company_id,
            OrderDocument.document_type == document_type,
            OrderDocument.deleted_at.is_(None),
        ]
        if locked_only:
            filters.append(OrderDocument.is_locked.is_(True))
        statement = (
            select(OrderDocument)
            .where(*filters)
            .order_by(OrderDocument.version.desc())
            .limit(1)
        )
        return self._db.scalar(statement)

    def soft_delete(self, document: OrderDocument) -> OrderDocument:
        document.deleted_at = datetime.now(tz=UTC)
        self._db.add(document)
        self._db.commit()
        self._db.refresh(document)
        return document
