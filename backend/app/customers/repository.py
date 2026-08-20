"""Customer persistence layer."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.customers.models import Customer, CustomerContact
from app.customers.schemas import (
    CustomerContactCreateRequest,
    CustomerContactUpdateRequest,
    CustomerCreateRequest,
    CustomerUpdateRequest,
)


class CustomerRepository:
    """Repository for customer records."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_id_for_company(
        self,
        customer_id: uuid.UUID,
        company_id: uuid.UUID,
    ) -> Customer | None:
        """Return a customer scoped to a company."""
        statement = select(Customer).where(
            Customer.id == customer_id,
            Customer.company_id == company_id,
            Customer.deleted_at.is_(None),
        )
        return self._db.scalar(statement)

    def list_for_company(
        self,
        company_id: uuid.UUID,
        *,
        page: int,
        page_size: int,
        search: str | None = None,
        is_active: bool | None = None,
    ) -> tuple[list[Customer], int]:
        """Return paginated customers for a company."""
        filters = [Customer.company_id == company_id, Customer.deleted_at.is_(None)]
        if is_active is not None:
            filters.append(Customer.is_active.is_(is_active))
        if search:
            pattern = f"%{search.strip()}%"
            filters.append(
                or_(
                    Customer.company_name.ilike(pattern),
                    Customer.vat_number.ilike(pattern),
                    Customer.street.ilike(pattern),
                    Customer.house_number.ilike(pattern),
                    Customer.postal_code.ilike(pattern),
                    Customer.address.ilike(pattern),
                    Customer.city.ilike(pattern),
                    Customer.country.ilike(pattern),
                    Customer.email.ilike(pattern),
                    Customer.invoice_email.ilike(pattern),
                    Customer.phone.ilike(pattern),
                    Customer.dispatch_phone.ilike(pattern),
                    Customer.notes.ilike(pattern),
                )
            )

        total = int(
            self._db.scalar(select(func.count()).select_from(Customer).where(*filters)) or 0
        )
        statement = (
            select(Customer)
            .where(*filters)
            .order_by(Customer.company_name.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(self._db.scalars(statement).all()), total

    def get_by_ids_for_company(
        self,
        customer_ids: set[uuid.UUID],
        company_id: uuid.UUID,
    ) -> dict[uuid.UUID, Customer]:
        """Return customers keyed by id for batch enrichment."""
        if not customer_ids:
            return {}
        statement = select(Customer).where(
            Customer.id.in_(customer_ids),
            Customer.company_id == company_id,
            Customer.deleted_at.is_(None),
        )
        customers = list(self._db.scalars(statement).all())
        return {customer.id: customer for customer in customers}

    def create(
        self,
        *,
        company_id: uuid.UUID,
        payload: CustomerCreateRequest,
        created_by: uuid.UUID,
    ) -> Customer:
        """Create a customer record."""
        customer = Customer(
            company_id=company_id,
            company_name=payload.company_name.strip(),
            vat_number=payload.vat_number,
            street=payload.street,
            house_number=payload.house_number,
            postal_code=payload.postal_code,
            address=payload.address,
            city=payload.city,
            country=payload.country,
            email=str(payload.email).lower() if payload.email else None,
            invoice_email=str(payload.invoice_email).lower() if payload.invoice_email else None,
            phone=payload.phone,
            dispatch_phone=payload.dispatch_phone,
            is_active=payload.is_active,
            notes=payload.notes,
            created_by=created_by,
            updated_by=created_by,
        )
        self._db.add(customer)
        self._db.commit()
        self._db.refresh(customer)
        return customer

    def update(
        self,
        customer: Customer,
        payload: CustomerUpdateRequest,
        updated_by: uuid.UUID,
    ) -> Customer:
        """Update a customer record."""
        customer.company_name = payload.company_name.strip()
        customer.vat_number = payload.vat_number
        customer.street = payload.street
        customer.house_number = payload.house_number
        customer.postal_code = payload.postal_code
        customer.address = payload.address
        customer.city = payload.city
        customer.country = payload.country
        customer.email = str(payload.email).lower() if payload.email else None
        customer.invoice_email = (
            str(payload.invoice_email).lower() if payload.invoice_email else None
        )
        customer.phone = payload.phone
        customer.dispatch_phone = payload.dispatch_phone
        customer.is_active = payload.is_active
        customer.notes = payload.notes
        customer.updated_by = updated_by
        self._db.add(customer)
        self._db.commit()
        self._db.refresh(customer)
        return customer

    def soft_delete(self, customer: Customer, deleted_by: uuid.UUID) -> Customer:
        """Soft delete a customer record."""
        customer.deleted_at = datetime.now(tz=UTC)
        customer.updated_by = deleted_by
        self._db.add(customer)
        self._db.commit()
        self._db.refresh(customer)
        return customer


class CustomerContactRepository:
    """Repository for customer contact records."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_id_for_customer(
        self,
        contact_id: uuid.UUID,
        customer_id: uuid.UUID,
        company_id: uuid.UUID,
    ) -> CustomerContact | None:
        """Return a contact scoped to a customer and company."""
        statement = select(CustomerContact).where(
            CustomerContact.id == contact_id,
            CustomerContact.customer_id == customer_id,
            CustomerContact.company_id == company_id,
            CustomerContact.deleted_at.is_(None),
        )
        return self._db.scalar(statement)

    def list_for_customer(
        self,
        customer_id: uuid.UUID,
        company_id: uuid.UUID,
    ) -> list[CustomerContact]:
        """Return contacts for a customer."""
        statement = (
            select(CustomerContact)
            .where(
                CustomerContact.customer_id == customer_id,
                CustomerContact.company_id == company_id,
                CustomerContact.deleted_at.is_(None),
            )
            .order_by(CustomerContact.is_primary.desc(), CustomerContact.last_name.asc())
        )
        return list(self._db.scalars(statement).all())

    def clear_primary_for_customer(
        self,
        customer_id: uuid.UUID,
        company_id: uuid.UUID,
        *,
        exclude_contact_id: uuid.UUID | None = None,
    ) -> None:
        """Unset primary flag on all contacts for a customer."""
        statement = select(CustomerContact).where(
            CustomerContact.customer_id == customer_id,
            CustomerContact.company_id == company_id,
            CustomerContact.deleted_at.is_(None),
            CustomerContact.is_primary.is_(True),
        )
        if exclude_contact_id is not None:
            statement = statement.where(CustomerContact.id != exclude_contact_id)

        contacts = list(self._db.scalars(statement).all())
        for contact in contacts:
            contact.is_primary = False
            self._db.add(contact)

    def create(
        self,
        *,
        company_id: uuid.UUID,
        customer_id: uuid.UUID,
        payload: CustomerContactCreateRequest,
        created_by: uuid.UUID,
    ) -> CustomerContact:
        """Create a customer contact record."""
        contact = CustomerContact(
            company_id=company_id,
            customer_id=customer_id,
            first_name=payload.first_name.strip(),
            last_name=payload.last_name.strip(),
            email=str(payload.email).lower() if payload.email else None,
            phone=payload.phone,
            job_title=payload.job_title,
            is_primary=payload.is_primary,
            notes=payload.notes,
            created_by=created_by,
            updated_by=created_by,
        )
        self._db.add(contact)
        self._db.commit()
        self._db.refresh(contact)
        return contact

    def update(
        self,
        contact: CustomerContact,
        payload: CustomerContactUpdateRequest,
        updated_by: uuid.UUID,
    ) -> CustomerContact:
        """Update a customer contact record."""
        contact.first_name = payload.first_name.strip()
        contact.last_name = payload.last_name.strip()
        contact.email = str(payload.email).lower() if payload.email else None
        contact.phone = payload.phone
        contact.job_title = payload.job_title
        contact.is_primary = payload.is_primary
        contact.notes = payload.notes
        contact.updated_by = updated_by
        self._db.add(contact)
        self._db.commit()
        self._db.refresh(contact)
        return contact

    def soft_delete(self, contact: CustomerContact, deleted_by: uuid.UUID) -> CustomerContact:
        """Soft delete a customer contact record."""
        contact.deleted_at = datetime.now(tz=UTC)
        contact.is_primary = False
        contact.updated_by = deleted_by
        self._db.add(contact)
        self._db.commit()
        self._db.refresh(contact)
        return contact
