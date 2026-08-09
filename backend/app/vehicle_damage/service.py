"""Vehicle damage business logic."""

import uuid

from sqlalchemy.orm import Session

from app.audit.service import AuditService
from app.common.enums import DamageSeverity, DamageType, UserRole
from app.common.execution_access import (
    ensure_execution_access,
    get_order_for_company,
    get_vehicle_for_order,
)
from app.common.exceptions import NotFoundError, ValidationError
from app.drivers.repository import DriverRepository
from app.notifications.service import NotificationService
from app.order_timeline.service import OrderTimelineService
from app.order_vehicles.repository import OrderVehicleRepository
from app.orders.repository import OrderRepository
from app.users.models import User
from app.realtime.publisher import publish_vehicle_execution_event
from app.realtime.schemas import RealtimeEventType
from app.vehicle_damage.models import VehicleDamage
from app.vehicle_damage.repository import VehicleDamageRepository
from app.vehicle_damage.schemas import (
    VehicleDamageCreateRequest,
    VehicleDamageResponse,
    VehicleDamageUpdateRequest,
)
from app.vehicle_photos.repository import VehiclePhotoRepository


class VehicleDamageService:
    """Vehicle damage reporting workflows."""

    def __init__(self, db: Session) -> None:
        self._damage = VehicleDamageRepository(db)
        self._photos = VehiclePhotoRepository(db)
        self._vehicles = OrderVehicleRepository(db)
        self._orders = OrderRepository(db)
        self._drivers = DriverRepository(db)
        self._timeline = OrderTimelineService(db)
        self._audit = AuditService(db)
        self._notifications = NotificationService(db)

    def list_damage(
        self,
        current_user: User,
        order_id: uuid.UUID,
        vehicle_id: uuid.UUID,
    ) -> list[VehicleDamageResponse]:
        order = get_order_for_company(self._orders, order_id, current_user.company_id)
        ensure_execution_access(current_user, order, self._drivers)
        get_vehicle_for_order(
            self._vehicles,
            order_id=order_id,
            vehicle_id=vehicle_id,
            company_id=current_user.company_id,
        )
        records = self._damage.list_for_vehicle(vehicle_id, current_user.company_id)
        return [self._to_response(record) for record in records]

    def create_damage(
        self,
        current_user: User,
        order_id: uuid.UUID,
        vehicle_id: uuid.UUID,
        payload: VehicleDamageCreateRequest,
        ip_address: str | None = None,
    ) -> VehicleDamageResponse:
        order = get_order_for_company(self._orders, order_id, current_user.company_id)
        ensure_execution_access(current_user, order, self._drivers)
        get_vehicle_for_order(
            self._vehicles,
            order_id=order_id,
            vehicle_id=vehicle_id,
            company_id=current_user.company_id,
        )
        self._validate_photo_ids(payload.photo_ids, current_user.company_id, vehicle_id)
        damage = self._damage.create(
            company_id=current_user.company_id,
            order_id=order_id,
            vehicle_id=vehicle_id,
            damage_type=payload.damage_type.value,
            severity=payload.severity.value,
            description=payload.description,
            location=payload.location,
            reported_by=current_user.id,
        )
        if payload.photo_ids:
            self._damage.replace_photos(damage.id, payload.photo_ids)
        self._timeline.record(
            current_user,
            order_id,
            "DAMAGE_REPORTED",
            f"Vehicle damage reported ({payload.damage_type.value}).",
        )
        self._audit.record_vehicle_damage_reported(
            company_id=current_user.company_id,
            user_id=current_user.id,
            entity_id=str(damage.id),
            ip_address=ip_address,
        )
        self._notifications.notify_staff(
            company_id=current_user.company_id,
            roles={UserRole.ADMIN, UserRole.DISPATCHER},
            title="Damage reported",
            message=f"Damage reported on order {order.order_number}.",
            notification_type="DAMAGE_REPORTED",
        )
        publish_vehicle_execution_event(
            company_id=current_user.company_id,
            order_id=order_id,
            vehicle_id=vehicle_id,
            event_type=RealtimeEventType.DAMAGE_REPORTED,
            order_number=order.order_number,
            extra={"damage_id": str(damage.id), "severity": payload.severity.value},
            driver_user_id=current_user.id,
        )
        return self._to_response(damage)

    def update_damage(
        self,
        current_user: User,
        damage_id: uuid.UUID,
        payload: VehicleDamageUpdateRequest,
        ip_address: str | None = None,
    ) -> VehicleDamageResponse:
        damage = self._damage.get_by_id_for_company(damage_id, current_user.company_id)
        if damage is None:
            raise NotFoundError(code="DAMAGE_NOT_FOUND", message="Damage report not found.")
        order = get_order_for_company(self._orders, damage.order_id, current_user.company_id)
        ensure_execution_access(current_user, order, self._drivers)
        self._validate_photo_ids(payload.photo_ids, current_user.company_id, damage.vehicle_id)
        updated = self._damage.update(
            damage,
            damage_type=payload.damage_type.value,
            severity=payload.severity.value,
            description=payload.description,
            location=payload.location,
        )
        self._damage.replace_photos(updated.id, payload.photo_ids)
        self._timeline.record(
            current_user,
            damage.order_id,
            "DAMAGE_UPDATED",
            "Vehicle damage report updated.",
        )
        return self._to_response(updated)

    def delete_damage(
        self,
        current_user: User,
        damage_id: uuid.UUID,
    ) -> None:
        damage = self._damage.get_by_id_for_company(damage_id, current_user.company_id)
        if damage is None:
            raise NotFoundError(code="DAMAGE_NOT_FOUND", message="Damage report not found.")
        order = get_order_for_company(self._orders, damage.order_id, current_user.company_id)
        ensure_execution_access(current_user, order, self._drivers)
        self._damage.soft_delete(damage)

    def _validate_photo_ids(
        self,
        photo_ids: list[uuid.UUID],
        company_id: uuid.UUID,
        vehicle_id: uuid.UUID,
    ) -> None:
        for photo_id in photo_ids:
            photo = self._photos.get_by_id_for_company(photo_id, company_id)
            if photo is None or photo.vehicle_id != vehicle_id:
                raise ValidationError(
                    code="INVALID_DAMAGE_PHOTO",
                    message="Attached photo must belong to the same vehicle.",
                )

    def _to_response(self, damage: VehicleDamage) -> VehicleDamageResponse:
        return VehicleDamageResponse(
            id=damage.id,
            company_id=damage.company_id,
            order_id=damage.order_id,
            vehicle_id=damage.vehicle_id,
            damage_type=DamageType(damage.damage_type),
            severity=DamageSeverity(damage.severity),
            description=damage.description,
            location=damage.location,
            reported_by=damage.reported_by,
            reported_at=damage.reported_at,
            photo_ids=self._damage.list_photo_ids(damage.id),
        )
