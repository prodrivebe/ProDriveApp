"""Order completion checklist database model."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from app.common.mixins import UUIDPrimaryKeyMixin
from app.database.base import Base


class OrderCompletionChecklist(Base, UUIDPrimaryKeyMixin):
    """Persisted completion checklist snapshot for an order."""

    __tablename__ = "order_completion_checklist"
    __table_args__ = (UniqueConstraint("order_id", name="uq_order_completion_checklist_order_id"),)

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
    pickup_completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    delivery_completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    vins_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    photos_uploaded: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    documents_uploaded: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    damage_reports_completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    can_complete: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    completion_percentage: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
