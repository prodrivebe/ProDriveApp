"""Driver database model."""

from __future__ import annotations

import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.common.mixins import SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin
from app.database.base import Base

if TYPE_CHECKING:
    from app.users.models import User


class Driver(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """Driver profile linked to an application user."""

    __tablename__ = "drivers"
    __table_args__ = (
        UniqueConstraint("company_id", "user_id", name="uq_drivers_company_user"),
    )

    company_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("companies.id"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    id_document_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    id_expiry: Mapped[date | None] = mapped_column(Date, nullable=True)
    driving_license: Mapped[str | None] = mapped_column(String(100), nullable=True)
    driving_licence_expiry: Mapped[date | None] = mapped_column(Date, nullable=True)
    adr_certificate: Mapped[str | None] = mapped_column(String(100), nullable=True)
    code95_expiry: Mapped[date | None] = mapped_column(Date, nullable=True)
    tachograph_card_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    tachograph_card_expiry: Mapped[date | None] = mapped_column(Date, nullable=True)
    visa_residence_expiry: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)

    user: Mapped[User] = relationship()
