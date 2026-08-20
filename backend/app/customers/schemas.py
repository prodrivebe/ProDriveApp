"""Customer API schemas."""

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CustomerResponse(BaseModel):
    """Customer response payload."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    company_name: str
    vat_number: str | None
    street: str | None
    house_number: str | None
    postal_code: str | None
    address: str | None
    city: str | None
    country: str | None
    email: str | None
    invoice_email: str | None
    phone: str | None
    dispatch_phone: str | None
    is_active: bool
    notes: str | None
    created_at: datetime
    updated_at: datetime


class CustomerCreateRequest(BaseModel):
    """Create customer payload."""

    company_name: str = Field(min_length=1, max_length=255)
    vat_number: str | None = Field(default=None, max_length=64)
    street: str | None = Field(default=None, max_length=255)
    house_number: str | None = Field(default=None, max_length=32)
    postal_code: str | None = Field(default=None, max_length=20)
    address: str | None = Field(default=None, max_length=500)
    city: str | None = Field(default=None, max_length=100)
    country: str | None = Field(default=None, max_length=100)
    email: EmailStr | None = None
    invoice_email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)
    dispatch_phone: str | None = Field(default=None, max_length=50)
    is_active: bool = True
    notes: str | None = Field(default=None, max_length=5000)


class CustomerUpdateRequest(BaseModel):
    """Update customer payload."""

    company_name: str = Field(min_length=1, max_length=255)
    vat_number: str | None = Field(default=None, max_length=64)
    street: str | None = Field(default=None, max_length=255)
    house_number: str | None = Field(default=None, max_length=32)
    postal_code: str | None = Field(default=None, max_length=20)
    address: str | None = Field(default=None, max_length=500)
    city: str | None = Field(default=None, max_length=100)
    country: str | None = Field(default=None, max_length=100)
    email: EmailStr | None = None
    invoice_email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)
    dispatch_phone: str | None = Field(default=None, max_length=50)
    is_active: bool = True
    notes: str | None = Field(default=None, max_length=5000)


class CustomerContactResponse(BaseModel):
    """Customer contact response payload."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    customer_id: uuid.UUID
    first_name: str
    last_name: str
    email: str | None
    phone: str | None
    job_title: str | None
    is_primary: bool
    notes: str | None
    created_at: datetime
    updated_at: datetime


class CustomerContactCreateRequest(BaseModel):
    """Create customer contact payload."""

    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)
    job_title: str | None = Field(default=None, max_length=100)
    is_primary: bool = False
    notes: str | None = Field(default=None, max_length=5000)


class CustomerContactUpdateRequest(BaseModel):
    """Update customer contact payload."""

    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)
    job_title: str | None = Field(default=None, max_length=100)
    is_primary: bool = False
    notes: str | None = Field(default=None, max_length=5000)


class CustomerHistoryEntry(BaseModel):
    """Placeholder customer history entry until orders are implemented."""

    id: uuid.UUID
    event_type: str
    description: str
    occurred_at: datetime
