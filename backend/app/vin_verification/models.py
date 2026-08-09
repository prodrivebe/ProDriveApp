"""VIN verification database models."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from app.common.mixins import UUIDPrimaryKeyMixin
from app.database.base import Base


class VinVerificationHistory(Base, UUIDPrimaryKeyMixin):
    """Immutable VIN verification and change history."""

    __tablename__ = "vin_verification_history"

    company_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("companies.id"),
        nullable=False,
        index=True,
    )
    order_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("orders.id"),
        nullable=False,
        index=True,
    )
    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("order_vehicles.id"),
        nullable=False,
        index=True,
    )
    original_vin: Mapped[str | None] = mapped_column(String(17), nullable=True)
    verified_vin: Mapped[str] = mapped_column(String(17), nullable=False)
    action: Mapped[str] = mapped_column(String(32), nullable=False)
    verified_by: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    verified_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
