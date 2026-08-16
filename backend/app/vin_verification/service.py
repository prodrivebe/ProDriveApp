"""VIN verification business logic."""

import uuid

from sqlalchemy.orm import Session

from app.audit.service import AuditService
from app.common.enums import UserRole, VinVerificationAction
from app.common.execution_access import (
    ensure_execution_access,
    get_order_for_company,
    get_vehicle_for_order,
)
from app.common.exceptions import ValidationError
from app.drivers.repository import DriverRepository
from app.notifications.service import NotificationService
from app.order_timeline.service import OrderTimelineService
from app.order_vehicles.repository import OrderVehicleRepository
from app.orders.repository import OrderRepository
from app.orders.validators import ensure_vehicles_editable, normalize_vin
from app.users.models import User
from app.realtime.publisher import publish_vehicle_execution_event
from app.realtime.schemas import RealtimeEventType
from app.vin_verification.repository import VinVerificationRepository
from app.vin_verification.schemas import VinVerificationResponse


class VinVerificationService:
    """VIN verification and immutable history workflows."""

    def __init__(self, db: Session) -> None:
        self._db = db
        self._history = VinVerificationRepository(db)
        self._vehicles = OrderVehicleRepository(db)
        self._orders = OrderRepository(db)
        self._drivers = DriverRepository(db)
        self._timeline = OrderTimelineService(db)
        self._audit = AuditService(db)
        self._notifications = NotificationService(db)

    def verify_vin(
        self,
        current_user: User,
        order_id: uuid.UUID,
        vehicle_id: uuid.UUID,
        vin: str,
        ip_address: str | None = None,
    ) -> VinVerificationResponse:
        """Verify and store a vehicle VIN."""
        normalized_vin = normalize_vin(vin)
        order = get_order_for_company(self._orders, order_id, current_user.company_id)
        ensure_execution_access(current_user, order, self._drivers)
        ensure_vehicles_editable(order)
        vehicle = get_vehicle_for_order(
            self._vehicles,
            order_id=order_id,
            vehicle_id=vehicle_id,
            company_id=current_user.company_id,
        )
        original_vin = vehicle.original_vin or vehicle.vin
        if vehicle.verified_vin is not None and vehicle.verified_vin == normalized_vin:
            return self._build_response(vehicle)

        if vehicle.original_vin is None:
            vehicle.original_vin = original_vin

        entry = self._history.create(
            company_id=current_user.company_id,
            order_id=order_id,
            vehicle_id=vehicle_id,
            original_vin=original_vin,
            verified_vin=normalized_vin,
            action=VinVerificationAction.VERIFIED,
            verified_by=current_user.id,
        )
        vehicle.verified_vin = normalized_vin
        vehicle.vin = normalized_vin
        vehicle.vin_verified_at = entry.verified_at
        vehicle.vin_verified_by = current_user.id
        self._db.add(vehicle)
        self._db.commit()
        self._db.refresh(vehicle)

        self._record_vin_event(
            current_user,
            order_id,
            vehicle_id,
            event_type="VIN_VERIFIED",
            description=f"VIN verified as {normalized_vin}.",
            audit_action="VIN_VERIFIED",
            old_value=original_vin,
            new_value=normalized_vin,
            ip_address=ip_address,
        )
        publish_vehicle_execution_event(
            company_id=current_user.company_id,
            order_id=order_id,
            vehicle_id=vehicle_id,
            event_type=RealtimeEventType.VIN_VERIFIED,
            order_number=order.order_number,
            extra={"vin": normalized_vin},
            driver_user_id=current_user.id if current_user.role == UserRole.DRIVER else None,
        )
        return self._build_response(vehicle)

    def update_vin(
        self,
        current_user: User,
        order_id: uuid.UUID,
        vehicle_id: uuid.UUID,
        vin: str,
        ip_address: str | None = None,
    ) -> VinVerificationResponse:
        """Change a verified VIN while preserving history."""
        normalized_vin = normalize_vin(vin)
        order = get_order_for_company(self._orders, order_id, current_user.company_id)
        ensure_execution_access(current_user, order, self._drivers)
        ensure_vehicles_editable(order)
        vehicle = get_vehicle_for_order(
            self._vehicles,
            order_id=order_id,
            vehicle_id=vehicle_id,
            company_id=current_user.company_id,
        )
        previous_vin = vehicle.verified_vin or vehicle.vin
        if previous_vin == normalized_vin:
            raise ValidationError(
                code="VIN_UNCHANGED",
                message="The submitted VIN matches the current value.",
            )

        original_vin = vehicle.original_vin or previous_vin
        if vehicle.original_vin is None:
            vehicle.original_vin = original_vin

        entry = self._history.create(
            company_id=current_user.company_id,
            order_id=order_id,
            vehicle_id=vehicle_id,
            original_vin=previous_vin,
            verified_vin=normalized_vin,
            action=VinVerificationAction.CHANGED,
            verified_by=current_user.id,
        )
        vehicle.verified_vin = normalized_vin
        vehicle.vin = normalized_vin
        vehicle.vin_verified_at = entry.verified_at
        vehicle.vin_verified_by = current_user.id
        self._db.add(vehicle)
        self._db.commit()
        self._db.refresh(vehicle)

        self._record_vin_event(
            current_user,
            order_id,
            vehicle_id,
            event_type="VIN_CHANGED",
            description=f"VIN changed from {previous_vin} to {normalized_vin}.",
            audit_action="VIN_CHANGED",
            old_value=previous_vin,
            new_value=normalized_vin,
            ip_address=ip_address,
        )
        self._notifications.notify_staff(
            company_id=current_user.company_id,
            roles={UserRole.ADMIN, UserRole.DISPATCHER},
            title="VIN changed",
            message=f"VIN changed on order {order.order_number}.",
            notification_type="VIN_CHANGED",
            order_id=order.id,
        )
        publish_vehicle_execution_event(
            company_id=current_user.company_id,
            order_id=order_id,
            vehicle_id=vehicle_id,
            event_type=RealtimeEventType.VIN_CHANGED,
            order_number=order.order_number,
            extra={"vin": normalized_vin},
            driver_user_id=current_user.id if current_user.role == UserRole.DRIVER else None,
        )
        return self._build_response(vehicle)

    def list_history(
        self,
        current_user: User,
        order_id: uuid.UUID,
        vehicle_id: uuid.UUID,
    ):
        """Return immutable VIN history for a vehicle."""
        order = get_order_for_company(self._orders, order_id, current_user.company_id)
        ensure_execution_access(current_user, order, self._drivers)
        get_vehicle_for_order(
            self._vehicles,
            order_id=order_id,
            vehicle_id=vehicle_id,
            company_id=current_user.company_id,
        )
        return self._history.list_for_vehicle(vehicle_id, current_user.company_id)

    def _record_vin_event(
        self,
        current_user: User,
        order_id: uuid.UUID,
        vehicle_id: uuid.UUID,
        *,
        event_type: str,
        description: str,
        audit_action: str,
        old_value: str | None,
        new_value: str,
        ip_address: str | None,
    ) -> None:
        self._timeline.record(current_user, order_id, event_type, description)
        self._audit.record_vin_verification(
            company_id=current_user.company_id,
            user_id=current_user.id,
            entity_id=str(vehicle_id),
            action=audit_action,
            old_value=old_value,
            new_value=new_value,
            ip_address=ip_address,
        )

    def _build_response(self, vehicle) -> VinVerificationResponse:
        return VinVerificationResponse(
            vehicle_id=vehicle.id,
            order_id=vehicle.order_id,
            vin=vehicle.vin,
            original_vin=vehicle.original_vin,
            verified_vin=vehicle.verified_vin,
            vin_verified_at=vehicle.vin_verified_at,
            vin_verified_by=vehicle.vin_verified_by,
        )

