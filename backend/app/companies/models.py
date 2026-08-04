"""Company database models."""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.common.mixins import TimestampMixin, UUIDPrimaryKeyMixin
from app.database.base import Base


class Company(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Tenant company record."""

    __tablename__ = "companies"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    vat_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    subscription_plan: Mapped[str | None] = mapped_column(String(100), nullable=True)

    users: Mapped[list["User"]] = relationship(back_populates="company")
    settings: Mapped["CompanySettings | None"] = relationship(
        back_populates="company",
        uselist=False,
    )


class CompanySettings(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Operational and branding settings for a tenant company."""

    __tablename__ = "company_settings"

    company_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("companies.id"),
        nullable=False,
        unique=True,
        index=True,
    )
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="UTC")
    default_currency: Mapped[str] = mapped_column(String(3), nullable=False, default="EUR")
    order_number_prefix: Mapped[str | None] = mapped_column(String(20), nullable=True)
    require_vehicle_photos: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    primary_color: Mapped[str] = mapped_column(String(7), nullable=False, default="#1B3A5F")
    secondary_color: Mapped[str] = mapped_column(
        String(7),
        nullable=False,
        default="#E8EEF4",
    )
    accent_color: Mapped[str] = mapped_column(String(7), nullable=False, default="#00A3E0")
    dashboard_title: Mapped[str | None] = mapped_column(String(255), nullable=True)

    company: Mapped["Company"] = relationship(back_populates="settings")
