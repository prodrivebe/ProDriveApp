"""Driver API schemas."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Self

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from app.orders.schemas import OrderSummaryResponse


class DriverResponse(BaseModel):
    """Driver profile response payload."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    user_id: uuid.UUID
    phone: str | None
    address: str | None
    country: str | None
    date_of_birth: date | None
    id_document_number: str | None
    id_expiry: date | None
    driving_license: str | None
    driving_licence_expiry: date | None
    adr_certificate: str | None
    code95_expiry: date | None
    tachograph_card_number: str | None
    tachograph_card_expiry: date | None
    visa_residence_expiry: date | None
    notes: str | None
    active: bool
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    display_name: str | None = None
    created_at: datetime
    updated_at: datetime


class DriverCreateRequest(BaseModel):
    """Create driver profile payload."""

    user_id: uuid.UUID | None = None
    first_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)
    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=8, max_length=128)
    phone: str | None = Field(default=None, max_length=50)
    address: str | None = Field(default=None, max_length=500)
    country: str | None = Field(default=None, max_length=100)
    date_of_birth: date | None = None
    id_document_number: str | None = Field(default=None, max_length=100)
    id_expiry: date | None = None
    driving_license: str | None = Field(default=None, max_length=100)
    driving_licence_expiry: date | None = None
    adr_certificate: str | None = Field(default=None, max_length=100)
    code95_expiry: date | None = None
    tachograph_card_number: str | None = Field(default=None, max_length=100)
    tachograph_card_expiry: date | None = None
    visa_residence_expiry: date | None = None
    notes: str | None = Field(default=None, max_length=1000)
    active: bool = True

    @model_validator(mode="after")
    def validate_user_source(self) -> Self:
        """Require either an existing user id or inline user creation fields."""
        has_user_id = self.user_id is not None
        has_inline_user = all(
            value is not None
            for value in (self.first_name, self.last_name, self.email, self.password)
        )
        if has_user_id and has_inline_user:
            raise ValueError("Provide either user_id or inline user fields, not both.")
        if not has_user_id and not has_inline_user:
            raise ValueError("Provide user_id or inline user fields.")
        return self


class DriverUpdateRequest(BaseModel):
    """Update driver profile payload."""

    first_name: str | None = Field(default=None, max_length=100)
    last_name: str | None = Field(default=None, max_length=100)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)
    address: str | None = Field(default=None, max_length=500)
    country: str | None = Field(default=None, max_length=100)
    date_of_birth: date | None = None
    id_document_number: str | None = Field(default=None, max_length=100)
    id_expiry: date | None = None
    driving_license: str | None = Field(default=None, max_length=100)
    driving_licence_expiry: date | None = None
    adr_certificate: str | None = Field(default=None, max_length=100)
    code95_expiry: date | None = None
    tachograph_card_number: str | None = Field(default=None, max_length=100)
    tachograph_card_expiry: date | None = None
    visa_residence_expiry: date | None = None
    notes: str | None = Field(default=None, max_length=1000)
    active: bool = True


class DriverHomeResponse(BaseModel):
    """Driver home screen payload."""

    driver: DriverResponse
    user_name: str
    truck_label: str | None = None
    trailer_label: str | None = None
    current_order: OrderSummaryResponse | None = None
    next_action: str
    unread_notifications: int = 0
