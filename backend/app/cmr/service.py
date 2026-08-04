"""CMR document business logic."""

import uuid

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.common.enums import DocumentType
from app.common.exceptions import NotFoundError
from app.common.storage.local import LocalFileStorage
from app.companies.repository import CompanyRepository
from app.config.settings import Settings
from app.cmr.generator import build_cmr_html
from app.customers.repository import CustomerRepository
from app.documents.models import Document
from app.documents.repository import DocumentRepository
from app.orders.service import OrderService
from app.users.models import User


class CmrService:
    """CMR generation and signed upload workflows."""

    def __init__(self, db: Session, settings: Settings) -> None:
        self._db = db
        self._settings = settings
        self._documents = DocumentRepository(db)
        self._orders = OrderService(db)
        self._companies = CompanyRepository(db)
        self._customers = CustomerRepository(db)
        self._storage = LocalFileStorage(settings)

    def generate_cmr(self, current_user: User, order_id: uuid.UUID) -> Document:
        """Generate a CMR document for an order."""
        order = self._orders.get_order(current_user, order_id)
        company = self._companies.get_by_id_for_company(current_user.company_id)
        if company is None:
            raise NotFoundError(code="COMPANY_NOT_FOUND", message="Company not found.")
        customer = self._customers.get_by_id_for_company(order.customer_id, order.company_id)
        if customer is None:
            raise NotFoundError(code="CUSTOMER_NOT_FOUND", message="Customer not found.")

        html_content = build_cmr_html(company=company, customer=customer, order=order)
        file_path = self._storage.save_order_document(
            company_id=current_user.company_id,
            order_id=order_id,
            filename=f"cmr-{order.order_number}.html",
            content=html_content.encode("utf-8"),
        )
        document = self._documents.create(
            company_id=current_user.company_id,
            order_id=order_id,
            document_type=DocumentType.CMR,
            file_path=file_path,
            generated_by=current_user.id,
        )
        self._orders.record_timeline_event(
            current_user,
            order_id,
            "CMR_GENERATED",
            f"CMR generated for order {order.order_number}.",
        )
        return document

    def get_cmr(self, current_user: User, order_id: uuid.UUID) -> Document:
        """Return the latest generated CMR for an order."""
        self._orders.get_order(current_user, order_id)
        document = self._documents.get_latest_for_order(
            order_id,
            current_user.company_id,
            DocumentType.CMR,
        )
        if document is None:
            raise NotFoundError(code="CMR_NOT_FOUND", message="CMR has not been generated yet.")
        return document

    def upload_signed_cmr(
        self,
        current_user: User,
        order_id: uuid.UUID,
        upload_file: UploadFile,
    ) -> Document:
        """Upload a signed CMR copy for an order."""
        order = self._orders.get_order(current_user, order_id)
        file_path = self._storage.save_signed_document(
            company_id=current_user.company_id,
            order_id=order_id,
            upload_file=upload_file,
        )
        document = self._documents.create(
            company_id=current_user.company_id,
            order_id=order_id,
            document_type=DocumentType.CMR_SIGNED,
            file_path=file_path,
            generated_by=current_user.id,
        )
        self._orders.record_timeline_event(
            current_user,
            order_id,
            "CMR_UPLOADED",
            f"Signed CMR uploaded for order {order.order_number}.",
        )
        return document
