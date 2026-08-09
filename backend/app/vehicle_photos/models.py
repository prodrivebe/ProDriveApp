"""Vehicle photo database model."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from app.common.enums import PhotoType
from app.common.mixins import UUIDPrimaryKeyMixin
from app.database.base import Base


class VehiclePhoto(Base, UUIDPrimaryKeyMixin):
    """Photo captured for a transported vehicle."""

    __tablename__ = "vehicle_photos"

    company_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("companies.id"),
        nullable=False,
        index=True,
    )
    order_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("orders.id"),
        nullable=True,
        index=True,
    )
    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("order_vehicles.id"),
        nullable=False,
        index=True,
    )
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    content_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    photo_type: Mapped[str] = mapped_column(String(32), nullable=False)
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    metadata_json: Mapped[str | None] = mapped_column("metadata", Text, nullable=True)
    gps_latitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 7), nullable=True)
    gps_longitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 7), nullable=True)

    @property
    def photo_type_enum(self) -> PhotoType:
        """Return the typed photo category."""
        return PhotoType(self.photo_type)
