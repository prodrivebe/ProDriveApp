"""Company API schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CompanyResponse(BaseModel):
    """Company profile response payload."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    vat_number: str | None
    address: str | None
    country: str | None
    phone: str | None
    email: EmailStr | None
    logo_url: str | None
    subscription_plan: str | None
    created_at: datetime
    updated_at: datetime


class CompanyUpdateRequest(BaseModel):
    """Company profile update payload."""

    name: str = Field(min_length=1, max_length=255)
    vat_number: str | None = Field(default=None, max_length=64)
    address: str | None = Field(default=None, max_length=500)
    country: str | None = Field(default=None, max_length=100)
    phone: str | None = Field(default=None, max_length=50)
    email: EmailStr | None = None
    subscription_plan: str | None = Field(default=None, max_length=100)


class CompanySettingsResponse(BaseModel):
    """Company settings and branding response payload."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    timezone: str
    default_currency: str
    order_number_prefix: str | None
    require_vehicle_photos: bool
    primary_color: str
    secondary_color: str
    accent_color: str
    dashboard_title: str | None
    created_at: datetime
    updated_at: datetime


class CompanySettingsUpdateRequest(BaseModel):
    """Company settings and branding update payload."""

    timezone: str = Field(default="UTC", max_length=64)
    default_currency: str = Field(default="EUR", min_length=3, max_length=3)
    order_number_prefix: str | None = Field(default=None, max_length=20)
    require_vehicle_photos: bool = True
    primary_color: str = Field(default="#1B3A5F", pattern=r"^#[0-9A-Fa-f]{6}$")
    secondary_color: str = Field(default="#E8EEF4", pattern=r"^#[0-9A-Fa-f]{6}$")
    accent_color: str = Field(default="#00A3E0", pattern=r"^#[0-9A-Fa-f]{6}$")
    dashboard_title: str | None = Field(default=None, max_length=255)


class CompanyLogoResponse(BaseModel):
    """Logo upload response payload."""

    logo_url: str
