"""Order database models."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.common.enums import OrderStatus, StopProgressStatus
from app.common.mixins import SoftDeleteMixin, TimestampMixin, UUIDPrimaryKeyMixin
from app.database.base import Base


class Order(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """Transport order header."""

    __tablename__ = "orders"
    __table_args__ = (
        UniqueConstraint("company_id", "order_number", name="uq_orders_company_order_number"),
    )

    company_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("companies.id"),
        nullable=False,
        index=True,
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("customers.id"),
        nullable=False,
        index=True,
    )
    order_number: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=OrderStatus.DRAFT,
        index=True,
    )
    assigned_driver_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("drivers.id"),
        nullable=True,
        index=True,
    )
    assigned_truck_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("trucks.id"),
        nullable=True,
    )
    assigned_trailer_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("trailers.id"),
        nullable=True,
    )
    planned_pickup_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    planned_delivery_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)

    stops: Mapped[list[OrderStop]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
    )
    vehicles: Mapped[list[OrderVehicle]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
    )
    timeline_entries: Mapped[list[OrderTimelineEntry]] = relationship(
        back_populates="order",
        cascade="all, delete-orphan",
    )


class OrderStop(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """Pickup or delivery stop on an order route."""

    __tablename__ = "order_stops"

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
    stop_type: Mapped[str] = mapped_column(String(16), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    company_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 7), nullable=True)
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 7), nullable=True)
    arrival_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    departure_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    progress_status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        default=StopProgressStatus.PENDING,
        index=True,
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)

    order: Mapped[Order] = relationship(back_populates="stops")


class OrderVehicle(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    """Vehicle transported on an order."""

    __tablename__ = "order_vehicles"

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
    pickup_stop_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("order_stops.id"),
        nullable=True,
    )
    delivery_stop_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("order_stops.id"),
        nullable=True,
    )
    vin: Mapped[str | None] = mapped_column(String(17), nullable=True, index=True)
    make: Mapped[str | None] = mapped_column(String(100), nullable=True)
    model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    generation: Mapped[str | None] = mapped_column(String(100), nullable=True)
    body_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    color: Mapped[str | None] = mapped_column(String(50), nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fuel_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    transmission: Mapped[str | None] = mapped_column(String(50), nullable=True)
    running: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    estimated_weight: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    estimated_height: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    original_vin: Mapped[str | None] = mapped_column(String(17), nullable=True)
    verified_vin: Mapped[str | None] = mapped_column(String(17), nullable=True)
    vin_verified_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    vin_verified_by: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)

    order: Mapped[Order] = relationship(back_populates="vehicles")


class OrderTimelineEntry(Base, UUIDPrimaryKeyMixin):
    """Chronological order activity entry."""

    __tablename__ = "order_timeline"

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
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    created_by: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    order: Mapped[Order] = relationship(back_populates="timeline_entries")
