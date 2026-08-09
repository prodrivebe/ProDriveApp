"""Order document business logic."""

import uuid

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.audit.service import AuditService
from app.common.enums import OrderDocumentType, UserRole
from app.common.exceptions import NotFoundError, ValidationError
from app.common.execution_access import ensure_execution_access, get_order_for_company
from app.common.storage.local import (
    ALLOWED_DOCUMENT_CONTENT_TYPES,
    LocalFileStorage,
)
from app.config.settings import Settings
from app.drivers.repository import DriverRepository
from app.notifications.service import NotificationService
from app.order_documents.models import OrderDocument
from app.order_documents.repository import OrderDocumentRepository
from app.order_timeline.service import OrderTimelineService
from app.orders.repository import OrderRepository
from app.users.models import User


class OrderDocumentService:
    """Versioned order document workflows."""

    def __init__(self, db: Session, settings: Settings) -> None:
        self._documents = OrderDocumentRepository(db)
        self._orders = OrderRepository(db)
        self._drivers = DriverRepository(db)
        self._timeline = OrderTimelineService(db)
        self._audit = AuditService(db)
        self._notifications = NotificationService(db)
        self._settings = settings
        self._storage = LocalFileStorage(settings)

    def list_documents(
        self,
        current_user: User,
        order_id: uuid.UUID,
    ) -> list[OrderDocument]:
        order = get_order_for_company(self._orders, order_id, current_user.company_id)
        ensure_execution_access(current_user, order, self._drivers)
        return self._documents.list_for_order(order_id, current_user.company_id)

    def get_document(
        self,
        current_user: User,
        document_id: uuid.UUID,
    ) -> OrderDocument:
        document = self._documents.get_by_id_for_company(document_id, current_user.company_id)
        if document is None:
            raise NotFoundError(code="DOCUMENT_NOT_FOUND", message="Document not found.")
        order = get_order_for_company(self._orders, document.order_id, current_user.company_id)
        ensure_execution_access(current_user, order, self._drivers)
        return document

    def upload_document(
        self,
        current_user: User,
        order_id: uuid.UUID,
        upload_file: UploadFile,
        *,
        document_type: OrderDocumentType,
        ip_address: str | None = None,
    ) -> OrderDocument:
        order = get_order_for_company(self._orders, order_id, current_user.company_id)
        ensure_execution_access(current_user, order, self._drivers)
        content = upload_file.file.read()
        content_type = upload_file.content_type or "application/octet-stream"
        if content_type not in ALLOWED_DOCUMENT_CONTENT_TYPES:
            raise ValidationError(
                code="INVALID_DOCUMENT_TYPE",
                message="Document must be a PNG, JPEG, WEBP, or PDF file.",
            )
        max_bytes = self._settings.max_document_size_mb * 1024 * 1024
        if len(content) > max_bytes:
            raise ValidationError(
                code="DOCUMENT_TOO_LARGE",
                message=(
                    f"Document must be smaller than {self._settings.max_document_size_mb} MB."
                ),
            )
        file_name = upload_file.filename or f"{document_type.value.lower()}.bin"
        file_path, _, _ = self._storage.save_order_document(
            company_id=current_user.company_id,
            order_id=order_id,
            filename=file_name,
            content=content,
            content_type=upload_file.content_type or "application/octet-stream",
        )
        next_version = self._documents.get_latest_version(
            order_id,
            current_user.company_id,
            document_type,
        ) + 1
        document = self._documents.create(
            company_id=current_user.company_id,
            order_id=order_id,
            document_type=document_type,
            file_path=file_path,
            file_name=file_name,
            version=next_version,
            uploaded_by=current_user.id,
        )
        event_type = "CMR_UPLOADED" if document_type == OrderDocumentType.CMR else "DOCUMENT_UPLOADED"
        if next_version > 1 and document_type == OrderDocumentType.CMR:
            self._timeline.record(
                current_user,
                order_id,
                "DOCUMENT_VERSION_CREATED",
                f"CMR version {next_version} uploaded.",
            )
        self._timeline.record(
            current_user,
            order_id,
            event_type,
            f"{document_type.value} document uploaded (v{next_version}).",
        )
        audit_action = "CMR_UPLOADED" if document_type == OrderDocumentType.CMR else "DOCUMENT_UPLOADED"
        self._audit.record_order_document_uploaded(
            company_id=current_user.company_id,
            user_id=current_user.id,
            entity_id=str(document.id),
            action=audit_action,
            ip_address=ip_address,
        )
        if document_type == OrderDocumentType.CMR:
            self._notifications.notify_staff(
                company_id=current_user.company_id,
                roles={UserRole.ADMIN, UserRole.DISPATCHER},
                title="CMR uploaded",
                message=f"CMR uploaded for order {order.order_number}.",
                notification_type="CMR_UPLOADED",
            )
        return document

    def delete_document(
        self,
        current_user: User,
        document_id: uuid.UUID,
    ) -> None:
        document = self.get_document(current_user, document_id)
        self._storage.delete_file(document.file_path)
        self._documents.soft_delete(document)

    def has_document_type(
        self,
        order_id: uuid.UUID,
        company_id: uuid.UUID,
        document_type: OrderDocumentType,
    ) -> bool:
        return self._documents.get_latest_version(order_id, company_id, document_type) > 0
