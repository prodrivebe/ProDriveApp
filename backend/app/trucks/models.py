"""Truck database model."""

import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from app.common.mixins import SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin
from app.database.base import Base


class Truck(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """Company truck record."""

    __tablename__ = "trucks"
    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "registration_number",
            name="uq_trucks_company_registration",
        ),
    )

    company_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("companies.id"),
        nullable=False,
        index=True,
    )
    registration_number: Mapped[str] = mapped_column(String(32), nullable=False)
    brand: Mapped[str | None] = mapped_column(String(100), nullable=True)
    model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    vin: Mapped[str | None] = mapped_column(String(32), nullable=True)
    capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
