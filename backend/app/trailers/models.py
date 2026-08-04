"""Trailer database model."""

import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from app.common.mixins import SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin
from app.database.base import Base


class Trailer(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """Company trailer record."""

    __tablename__ = "trailers"
    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "registration_number",
            name="uq_trailers_company_registration",
        ),
    )

    company_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("companies.id"),
        nullable=False,
        index=True,
    )
    registration_number: Mapped[str] = mapped_column(String(32), nullable=False)
    manufacturer: Mapped[str | None] = mapped_column(String(100), nullable=True)
    model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    trailer_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    maximum_height: Mapped[float | None] = mapped_column(Numeric(8, 2), nullable=True)
    maximum_weight: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    maximum_vehicle_count: Mapped[int] = mapped_column(Integer, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
