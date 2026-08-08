"""Fleet assignment persistence layer."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.fleet.models import FleetAssignment


class FleetAssignmentRepository:
    """Repository for fleet assignment records."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def list_for_company(
        self,
        company_id: uuid.UUID,
        *,
        active_only: bool = False,
    ) -> list[FleetAssignment]:
        """Return assignments for a company."""
        filters = [FleetAssignment.company_id == company_id]
        if active_only:
            filters.append(FleetAssignment.active.is_(True))
        statement = (
            select(FleetAssignment)
            .where(*filters)
            .order_by(FleetAssignment.assigned_at.desc())
        )
        return list(self._db.scalars(statement).all())

    def get_by_id_for_company(
        self,
        assignment_id: uuid.UUID,
        company_id: uuid.UUID,
    ) -> FleetAssignment | None:
        """Return an assignment scoped to a company."""
        statement = select(FleetAssignment).where(
            FleetAssignment.id == assignment_id,
            FleetAssignment.company_id == company_id,
        )
        return self._db.scalar(statement)

    def get_active_for_driver(
        self,
        driver_id: uuid.UUID,
        company_id: uuid.UUID,
    ) -> FleetAssignment | None:
        """Return the active assignment for a driver."""
        statement = select(FleetAssignment).where(
            FleetAssignment.driver_id == driver_id,
            FleetAssignment.company_id == company_id,
            FleetAssignment.active.is_(True),
        )
        return self._db.scalar(statement)

    def get_active_for_truck(
        self,
        truck_id: uuid.UUID,
        company_id: uuid.UUID,
    ) -> FleetAssignment | None:
        """Return the active assignment for a truck."""
        statement = select(FleetAssignment).where(
            FleetAssignment.truck_id == truck_id,
            FleetAssignment.company_id == company_id,
            FleetAssignment.active.is_(True),
        )
        return self._db.scalar(statement)

    def get_active_for_trailer(
        self,
        trailer_id: uuid.UUID,
        company_id: uuid.UUID,
    ) -> FleetAssignment | None:
        """Return the active assignment for a trailer."""
        statement = select(FleetAssignment).where(
            FleetAssignment.trailer_id == trailer_id,
            FleetAssignment.company_id == company_id,
            FleetAssignment.active.is_(True),
        )
        return self._db.scalar(statement)

    def create(
        self,
        *,
        company_id: uuid.UUID,
        driver_id: uuid.UUID,
        truck_id: uuid.UUID,
        trailer_id: uuid.UUID,
    ) -> FleetAssignment:
        """Create an active fleet assignment."""
        now = datetime.now(tz=UTC)
        assignment = FleetAssignment(
            company_id=company_id,
            driver_id=driver_id,
            truck_id=truck_id,
            trailer_id=trailer_id,
            assigned_at=now,
            active=True,
        )
        self._db.add(assignment)
        self._db.commit()
        self._db.refresh(assignment)
        return assignment

    def deactivate(self, assignment: FleetAssignment) -> FleetAssignment:
        """Mark an assignment as inactive."""
        assignment.active = False
        assignment.unassigned_at = datetime.now(tz=UTC)
        self._db.add(assignment)
        self._db.commit()
        self._db.refresh(assignment)
        return assignment
