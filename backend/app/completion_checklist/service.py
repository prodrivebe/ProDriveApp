"""Completion checklist business logic."""

import uuid

from sqlalchemy.orm import Session

from app.common.enums import OrderDocumentType, PhotoType, StopProgressStatus, StopType, UserRole
from app.common.exceptions import NotFoundError, ValidationError
from app.common.execution_access import ensure_execution_access, get_order_for_company
from app.companies.repository import CompanyRepository
from app.completion_checklist.repository import CompletionChecklistRepository
from app.completion_checklist.schemas import (
    CompletionChecklistResponse,
    CompletionValidationResponse,
)
from app.drivers.repository import DriverRepository
from app.notifications.service import NotificationService
from app.order_documents.repository import OrderDocumentRepository
from app.order_stops.repository import OrderStopRepository
from app.order_timeline.service import OrderTimelineService
from app.order_vehicles.repository import OrderVehicleRepository
from app.orders.repository import OrderRepository
from app.users.models import User
from app.vehicle_damage.repository import VehicleDamageRepository
from app.vehicle_photos.repository import VehiclePhotoRepository

REQUIRED_PHOTO_TYPES = {
    PhotoType.FRONT,
    PhotoType.REAR,
    PhotoType.LEFT,
    PhotoType.RIGHT,
}
CHECKLIST_ITEMS = (
    "pickup_completed",
    "delivery_completed",
    "vins_verified",
    "photos_uploaded",
    "documents_uploaded",
    "damage_reports_completed",
)


class CompletionChecklistService:
    """Order completion checklist computation and validation."""

    def __init__(self, db: Session) -> None:
        self._checklists = CompletionChecklistRepository(db)
        self._orders = OrderRepository(db)
        self._stops = OrderStopRepository(db)
        self._vehicles = OrderVehicleRepository(db)
        self._photos = VehiclePhotoRepository(db)
        self._documents = OrderDocumentRepository(db)
        self._damage = VehicleDamageRepository(db)
        self._companies = CompanyRepository(db)
        self._drivers = DriverRepository(db)
        self._timeline = OrderTimelineService(db)
        self._notifications = NotificationService(db)

    def get_checklist(
        self,
        current_user: User,
        order_id: uuid.UUID,
    ) -> CompletionChecklistResponse:
        order = get_order_for_company(self._orders, order_id, current_user.company_id)
        ensure_execution_access(current_user, order, self._drivers)
        return self._compute_and_store(current_user, order_id)

    def validate_completion(
        self,
        current_user: User,
        order_id: uuid.UUID,
    ) -> CompletionValidationResponse:
        order = get_order_for_company(self._orders, order_id, current_user.company_id)
        ensure_execution_access(current_user, order, self._drivers)
        checklist = self._compute_and_store(current_user, order_id)
        self._timeline.record(
            current_user,
            order_id,
            "COMPLETION_VALIDATED",
            f"Completion checklist validated at {checklist.completion_percentage}%.",
        )
        if checklist.can_complete:
            self._notifications.notify_staff(
                company_id=current_user.company_id,
                roles={UserRole.ADMIN, UserRole.DISPATCHER},
                title="Order ready for completion",
                message=f"Order {order.order_number} passed completion validation.",
                notification_type="ORDER_READY_FOR_COMPLETION",
            )
        return CompletionValidationResponse.model_validate(checklist.model_dump())

    def enforce_completion_ready(
        self,
        current_user: User,
        order_id: uuid.UUID,
    ) -> None:
        """Raise when the order cannot be marked completed."""
        checklist = self._compute_and_store(current_user, order_id)
        if not checklist.can_complete:
            raise ValidationError(
                code="CHECKLIST_INCOMPLETE",
                message=(
                    "Order completion checklist is incomplete. "
                    f"Missing: {', '.join(checklist.missing_items)}."
                ),
            )

    def _compute_and_store(
        self,
        current_user: User,
        order_id: uuid.UUID,
    ) -> CompletionChecklistResponse:
        company_id = current_user.company_id
        stops = self._stops.list_for_order(order_id, company_id)
        vehicles = self._vehicles.list_for_order(order_id, company_id)
        settings = self._companies.get_settings_for_company(company_id)

        pickup_stops = [stop for stop in stops if stop.stop_type == StopType.PICKUP]
        delivery_stops = [stop for stop in stops if stop.stop_type == StopType.DELIVERY]
        pickup_completed = not pickup_stops or all(
            StopProgressStatus(stop.progress_status) == StopProgressStatus.COMPLETED
            for stop in pickup_stops
        )
        delivery_completed = not delivery_stops or all(
            StopProgressStatus(stop.progress_status) == StopProgressStatus.COMPLETED
            for stop in delivery_stops
        )
        vins_verified = not vehicles or all(vehicle.verified_vin for vehicle in vehicles)

        photos_uploaded = True
        if settings and settings.require_vehicle_photos:
            for vehicle in vehicles:
                photos = self._photos.list_for_vehicle(vehicle.id, company_id)
                uploaded_types = {PhotoType(photo.photo_type) for photo in photos}
                if not REQUIRED_PHOTO_TYPES.issubset(uploaded_types):
                    photos_uploaded = False
                    break

        documents_uploaded = (
            self._documents.get_latest_version(order_id, company_id, OrderDocumentType.CMR) > 0
        )

        damage_reports_completed = True
        for vehicle in vehicles:
            for damage in self._damage.list_for_vehicle(vehicle.id, company_id):
                if not damage.description:
                    damage_reports_completed = False
                    break
            if not damage_reports_completed:
                break

        flags = {
            "pickup_completed": pickup_completed,
            "delivery_completed": delivery_completed,
            "vins_verified": vins_verified,
            "photos_uploaded": photos_uploaded,
            "documents_uploaded": documents_uploaded,
            "damage_reports_completed": damage_reports_completed,
        }
        completed_items = [name for name, done in flags.items() if done]
        missing_items = [name for name, done in flags.items() if not done]
        completion_percentage = int(len(completed_items) / len(CHECKLIST_ITEMS) * 100)
        can_complete = len(missing_items) == 0

        self._checklists.upsert(
            company_id=company_id,
            order_id=order_id,
            pickup_completed=pickup_completed,
            delivery_completed=delivery_completed,
            vins_verified=vins_verified,
            photos_uploaded=photos_uploaded,
            documents_uploaded=documents_uploaded,
            damage_reports_completed=damage_reports_completed,
            can_complete=can_complete,
            completion_percentage=completion_percentage,
        )
        return CompletionChecklistResponse(
            pickup_completed=pickup_completed,
            delivery_completed=delivery_completed,
            vins_verified=vins_verified,
            photos_uploaded=photos_uploaded,
            documents_uploaded=documents_uploaded,
            damage_reports_completed=damage_reports_completed,
            can_complete=can_complete,
            completion_percentage=completion_percentage,
            completed_items=completed_items,
            missing_items=missing_items,
        )
