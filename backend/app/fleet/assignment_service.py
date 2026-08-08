"""Fleet assignment business logic."""

import uuid

from sqlalchemy.orm import Session

from app.audit.service import AuditService
from app.common.enums import UserRole
from app.common.exceptions import NotFoundError, ValidationError
from app.common.tenant import ensure_same_company
from app.drivers.repository import DriverRepository
from app.fleet.assignment_repository import FleetAssignmentRepository
from app.fleet.models import FleetAssignment
from app.fleet.schemas import FleetAssignmentCreateRequest
from app.trailers.repository import TrailerRepository
from app.trucks.repository import TruckRepository
from app.users.models import User


class FleetAssignmentService:
    """Standing fleet assignment workflows."""

    def __init__(self, db: Session) -> None:
        self._db = db
        self._repository = FleetAssignmentRepository(db)
        self._drivers = DriverRepository(db)
        self._trucks = TruckRepository(db)
        self._trailers = TrailerRepository(db)
        self._audit_service = AuditService(db)

    def list_assignments(
        self,
        current_user: User,
        *,
        active_only: bool = False,
    ) -> list[FleetAssignment]:
        """List fleet assignments for the current company."""
        return self._repository.list_for_company(
            current_user.company_id,
            active_only=active_only,
        )

    def get_assignment(
        self,
        current_user: User,
        assignment_id: uuid.UUID,
    ) -> FleetAssignment:
        """Return an assignment in the current company."""
        assignment = self._repository.get_by_id_for_company(
            assignment_id,
            current_user.company_id,
        )
        if assignment is None:
            raise NotFoundError(
                code="ASSIGNMENT_NOT_FOUND",
                message="Fleet assignment not found.",
            )
        ensure_same_company(assignment.company_id, current_user)
        return assignment

    def get_my_assignment(self, current_user: User) -> FleetAssignment:
        """Return the active assignment for the current driver."""
        if current_user.role != UserRole.DRIVER:
            raise ValidationError(
                code="NOT_A_DRIVER",
                message="Current user is not a driver.",
            )
        driver = self._drivers.get_by_user_for_company(
            current_user.id,
            current_user.company_id,
        )
        if driver is None:
            raise NotFoundError(
                code="DRIVER_NOT_FOUND",
                message="Driver profile not found.",
            )
        assignment = self._repository.get_active_for_driver(
            driver.id,
            current_user.company_id,
        )
        if assignment is None:
            raise NotFoundError(
                code="ASSIGNMENT_NOT_FOUND",
                message="No active fleet assignment found.",
            )
        return assignment

    def create_assignment(
        self,
        current_user: User,
        payload: FleetAssignmentCreateRequest,
        ip_address: str | None,
    ) -> FleetAssignment:
        """Create a standing fleet assignment."""
        company_id = current_user.company_id
        driver = self._drivers.get_by_id_for_company(payload.driver_id, company_id)
        if driver is None:
            raise NotFoundError(code="DRIVER_NOT_FOUND", message="Driver not found.")
        truck = self._trucks.get_by_id_for_company(payload.truck_id, company_id)
        if truck is None:
            raise NotFoundError(code="TRUCK_NOT_FOUND", message="Truck not found.")
        trailer = self._trailers.get_by_id_for_company(payload.trailer_id, company_id)
        if trailer is None:
            raise NotFoundError(code="TRAILER_NOT_FOUND", message="Trailer not found.")

        if not driver.active:
            raise ValidationError(
                code="DRIVER_INACTIVE",
                message="Cannot assign an inactive driver.",
            )
        if not truck.active:
            raise ValidationError(
                code="TRUCK_INACTIVE",
                message="Cannot assign an inactive truck.",
            )
        if not trailer.active:
            raise ValidationError(
                code="TRAILER_INACTIVE",
                message="Cannot assign an inactive trailer.",
            )

        if self._repository.get_active_for_driver(payload.driver_id, company_id):
            raise ValidationError(
                code="DRIVER_ALREADY_ASSIGNED",
                message="Driver already has an active fleet assignment.",
            )
        if self._repository.get_active_for_truck(payload.truck_id, company_id):
            raise ValidationError(
                code="TRUCK_ALREADY_ASSIGNED",
                message="Truck already has an active fleet assignment.",
            )
        if self._repository.get_active_for_trailer(payload.trailer_id, company_id):
            raise ValidationError(
                code="TRAILER_ALREADY_ASSIGNED",
                message="Trailer already has an active fleet assignment.",
            )

        assignment = self._repository.create(
            company_id=company_id,
            driver_id=payload.driver_id,
            truck_id=payload.truck_id,
            trailer_id=payload.trailer_id,
        )
        self._audit_service.record_assignment_created(
            company_id=company_id,
            user_id=current_user.id,
            entity_id=str(assignment.id),
            ip_address=ip_address,
        )
        return assignment

    def remove_assignment(
        self,
        current_user: User,
        assignment_id: uuid.UUID,
        ip_address: str | None,
    ) -> FleetAssignment:
        """Deactivate a fleet assignment."""
        assignment = self.get_assignment(current_user, assignment_id)
        if not assignment.active:
            raise ValidationError(
                code="ASSIGNMENT_ALREADY_INACTIVE",
                message="Fleet assignment is already inactive.",
            )
        deactivated = self._repository.deactivate(assignment)
        self._audit_service.record_assignment_removed(
            company_id=current_user.company_id,
            user_id=current_user.id,
            entity_id=str(deactivated.id),
            ip_address=ip_address,
        )
        return deactivated
