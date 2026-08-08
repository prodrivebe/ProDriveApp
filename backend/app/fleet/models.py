"""Fleet assignment database model."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from app.common.mixins import UUIDPrimaryKeyMixin
from app.database.base import Base


class FleetAssignment(Base, UUIDPrimaryKeyMixin):
    """Standing assignment of a driver to a truck and trailer."""

    __tablename__ = "fleet_assignments"
    __table_args__ = (
        Index(
            "uq_fleet_assignments_active_driver",
            "company_id",
            "driver_id",
            unique=True,
            postgresql_where="active IS TRUE",
        ),
        Index(
            "uq_fleet_assignments_active_truck",
            "company_id",
            "truck_id",
            unique=True,
            postgresql_where="active IS TRUE",
        ),
        Index(
            "uq_fleet_assignments_active_trailer",
            "company_id",
            "trailer_id",
            unique=True,
            postgresql_where="active IS TRUE",
        ),
    )

    company_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("companies.id"),
        nullable=False,
        index=True,
    )
    driver_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("drivers.id"),
        nullable=False,
        index=True,
    )
    truck_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("trucks.id"),
        nullable=False,
        index=True,
    )
    trailer_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("trailers.id"),
        nullable=False,
        index=True,
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    unassigned_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
