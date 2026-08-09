"""Loading plan and position database models."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.common.mixins import TimestampMixin, UUIDPrimaryKeyMixin
from app.database.base import Base


class LoadingPlan(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Persisted trailer loading plan for an order."""

    __tablename__ = "loading_plans"

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
    trailer_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    route_sequence_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    estimated_total_height: Mapped[float | None] = mapped_column(Numeric(8, 2), nullable=True)
    estimated_total_weight: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    estimated_travel_km: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    front_axle_percent: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    rear_axle_percent: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    validation_warnings_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_generated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    confirmed_by: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)

    positions: Mapped[list[LoadingPosition]] = relationship(
        back_populates="loading_plan",
        cascade="all, delete-orphan",
    )


class LoadingPosition(Base, UUIDPrimaryKeyMixin):
    """Vehicle position on a trailer loading plan."""

    __tablename__ = "loading_positions"

    company_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("companies.id"),
        nullable=False,
        index=True,
    )
    loading_plan_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("loading_plans.id"),
        nullable=False,
        index=True,
    )
    vehicle_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("order_vehicles.id"),
        nullable=False,
        index=True,
    )
    upper_deck: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    trailer_position: Mapped[int] = mapped_column(Integer, nullable=False)
    loading_order: Mapped[int] = mapped_column(Integer, nullable=False)
    unloading_order: Mapped[int] = mapped_column(Integer, nullable=False)
    destination_city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    confirmed_by_dispatcher: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ai_generated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    loading_plan: Mapped[LoadingPlan] = relationship(back_populates="positions")
