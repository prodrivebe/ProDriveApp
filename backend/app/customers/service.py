"""Customer business logic."""

import uuid

from sqlalchemy.orm import Session

from app.audit.service import AuditService
from app.common.enums import OrderStatus
from app.common.exceptions import NotFoundError, ValidationError
from app.common.tenant import ensure_same_company
from app.customers.models import Customer, CustomerContact
from app.customers.repository import CustomerContactRepository, CustomerRepository
from app.customers.schemas import (
    CustomerContactCreateRequest,
    CustomerContactUpdateRequest,
    CustomerCreateRequest,
    CustomerUpdateRequest,
)
from app.orders.repository import OrderRepository
from app.orders.schemas import OrderSummaryResponse
from app.users.models import User

MAX_PAGE_SIZE = 100


class CustomerService:
    """Customer management workflows."""

    def __init__(self, db: Session) -> None:
        self._db = db
        self._repository = CustomerRepository(db)
        self._contacts = CustomerContactRepository(db)
        self._orders = OrderRepository(db)
        self._audit_service = AuditService(db)

    def list_customers(
        self,
        current_user: User,
        *,
        page: int,
        page_size: int,
        search: str | None,
        is_active: bool | None = None,
    ) -> tuple[list[Customer], int]:
        """List customers for the current company."""
        normalized_page = max(page, 1)
        normalized_page_size = min(max(page_size, 1), MAX_PAGE_SIZE)
        return self._repository.list_for_company(
            current_user.company_id,
            page=normalized_page,
            page_size=normalized_page_size,
            search=search,
            is_active=is_active,
        )

    def get_customer(self, current_user: User, customer_id: uuid.UUID) -> Customer:
        """Return a customer in the current company."""
        customer = self._repository.get_by_id_for_company(
            customer_id,
            current_user.company_id,
        )
        if customer is None:
            raise NotFoundError(code="CUSTOMER_NOT_FOUND", message="Customer not found.")
        ensure_same_company(customer.company_id, current_user)
        return customer

    def create_customer(
        self,
        current_user: User,
        payload: CustomerCreateRequest,
        ip_address: str | None,
    ) -> Customer:
        """Create a customer in the current company."""
        customer = self._repository.create(
            company_id=current_user.company_id,
            payload=payload,
            created_by=current_user.id,
        )
        self._audit_service.record_customer_created(
            company_id=current_user.company_id,
            user_id=current_user.id,
            entity_id=str(customer.id),
            ip_address=ip_address,
        )
        return customer

    def update_customer(
        self,
        current_user: User,
        customer_id: uuid.UUID,
        payload: CustomerUpdateRequest,
        ip_address: str | None,
    ) -> Customer:
        """Update a customer in the current company."""
        customer = self.get_customer(current_user, customer_id)
        updated_customer = self._repository.update(customer, payload, current_user.id)
        self._audit_service.record_customer_updated(
            company_id=current_user.company_id,
            user_id=current_user.id,
            entity_id=str(customer.id),
            ip_address=ip_address,
        )
        return updated_customer

    def delete_customer(
        self,
        current_user: User,
        customer_id: uuid.UUID,
        ip_address: str | None,
    ) -> None:
        """Soft delete a customer in the current company."""
        customer = self.get_customer(current_user, customer_id)
        order_count = self._orders.count_for_customer(
            current_user.company_id,
            customer_id,
        )
        if order_count > 0:
            raise ValidationError(
                code="CUSTOMER_HAS_ORDERS",
                message="Cannot delete a customer with existing orders.",
            )
        self._repository.soft_delete(customer, current_user.id)
        self._audit_service.record_customer_deleted(
            company_id=current_user.company_id,
            user_id=current_user.id,
            entity_id=str(customer.id),
            ip_address=ip_address,
        )

    def list_customer_contacts(
        self,
        current_user: User,
        customer_id: uuid.UUID,
    ) -> list[CustomerContact]:
        """List contacts for a customer."""
        self.get_customer(current_user, customer_id)
        return self._contacts.list_for_customer(customer_id, current_user.company_id)

    def create_customer_contact(
        self,
        current_user: User,
        customer_id: uuid.UUID,
        payload: CustomerContactCreateRequest,
        ip_address: str | None,
    ) -> CustomerContact:
        """Create a contact for a customer."""
        self.get_customer(current_user, customer_id)
        if payload.is_primary:
            self._contacts.clear_primary_for_customer(
                customer_id,
                current_user.company_id,
            )

        contact = self._contacts.create(
            company_id=current_user.company_id,
            customer_id=customer_id,
            payload=payload,
            created_by=current_user.id,
        )
        self._audit_service.record_customer_contact_created(
            company_id=current_user.company_id,
            user_id=current_user.id,
            entity_id=str(contact.id),
            ip_address=ip_address,
        )
        return contact

    def update_customer_contact(
        self,
        current_user: User,
        customer_id: uuid.UUID,
        contact_id: uuid.UUID,
        payload: CustomerContactUpdateRequest,
        ip_address: str | None,
    ) -> CustomerContact:
        """Update a customer contact."""
        self.get_customer(current_user, customer_id)
        contact = self._contacts.get_by_id_for_customer(
            contact_id,
            customer_id,
            current_user.company_id,
        )
        if contact is None:
            raise NotFoundError(
                code="CUSTOMER_CONTACT_NOT_FOUND",
                message="Customer contact not found.",
            )

        if payload.is_primary:
            self._contacts.clear_primary_for_customer(
                customer_id,
                current_user.company_id,
                exclude_contact_id=contact.id,
            )

        updated_contact = self._contacts.update(contact, payload, current_user.id)
        self._audit_service.record_customer_contact_updated(
            company_id=current_user.company_id,
            user_id=current_user.id,
            entity_id=str(contact.id),
            ip_address=ip_address,
        )
        return updated_contact

    def delete_customer_contact(
        self,
        current_user: User,
        customer_id: uuid.UUID,
        contact_id: uuid.UUID,
        ip_address: str | None,
    ) -> None:
        """Soft delete a customer contact."""
        self.get_customer(current_user, customer_id)
        contact = self._contacts.get_by_id_for_customer(
            contact_id,
            customer_id,
            current_user.company_id,
        )
        if contact is None:
            raise NotFoundError(
                code="CUSTOMER_CONTACT_NOT_FOUND",
                message="Customer contact not found.",
            )

        self._contacts.soft_delete(contact, current_user.id)
        self._audit_service.record_customer_contact_deleted(
            company_id=current_user.company_id,
            user_id=current_user.id,
            entity_id=str(contact.id),
            ip_address=ip_address,
        )

    def list_customer_history(
        self,
        current_user: User,
        customer_id: uuid.UUID,
    ) -> tuple[list[OrderSummaryResponse], int]:
        """Return customer order history."""
        self.get_customer(current_user, customer_id)
        orders, total = self._orders.list_for_company(
            current_user.company_id,
            page=1,
            page_size=MAX_PAGE_SIZE,
            customer_id=customer_id,
        )
        summaries = [
            OrderSummaryResponse(
                id=order.id,
                order_number=order.order_number,
                status=OrderStatus(order.status),
                customer_id=order.customer_id,
                planned_pickup_date=order.planned_pickup_date,
                planned_delivery_date=order.planned_delivery_date,
                created_at=order.created_at,
            )
            for order in orders
        ]
        return summaries, total
