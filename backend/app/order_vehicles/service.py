"""Order vehicle business logic."""

import uuid

from sqlalchemy.orm import Session

from app.audit.service import AuditService
from app.common.exceptions import NotFoundError
from app.order_stops.repository import OrderStopRepository
from app.order_timeline.service import OrderTimelineService
from app.order_vehicles.repository import OrderVehicleRepository
from app.order_vehicles.schemas import OrderVehicleCreateRequest, OrderVehicleUpdateRequest
from app.orders.models import OrderVehicle
from app.orders.repository import OrderRepository
from app.orders.validators import normalize_vin, validate_order_editable, validate_vehicle_stop_links
from app.users.models import User


class OrderVehicleService:
    """Order vehicle management workflows."""

    def __init__(self, db: Session) -> None:
        self._vehicles = OrderVehicleRepository(db)
        self._stops = OrderStopRepository(db)
        self._orders = OrderRepository(db)
        self._timeline = OrderTimelineService(db)
        self._audit = AuditService(db)

    def _get_editable_order(self, current_user: User, order_id: uuid.UUID):
        order = self._orders.get_by_id_for_company(order_id, current_user.company_id)
        if order is None:
            raise NotFoundError(code="ORDER_NOT_FOUND", message="Order not found.")
        validate_order_editable(order)
        return order

    def list_vehicles(self, current_user: User, order_id: uuid.UUID) -> list[OrderVehicle]:
        """List vehicles for an order."""
        order = self._orders.get_by_id_for_company(order_id, current_user.company_id)
        if order is None:
            raise NotFoundError(code="ORDER_NOT_FOUND", message="Order not found.")
        return self._vehicles.list_for_order(order_id, current_user.company_id)

    def create_vehicle(
        self,
        current_user: User,
        order_id: uuid.UUID,
        payload: OrderVehicleCreateRequest,
        ip_address: str | None,
    ) -> OrderVehicle:
        """Create a vehicle on an order."""
        self._get_editable_order(current_user, order_id)
        stops = self._stops.list_for_order(order_id, current_user.company_id)
        validate_vehicle_stop_links(stops, payload)
        vin = normalize_vin(payload.vin) if payload.vin else None
        vehicle = self._vehicles.create(
            company_id=current_user.company_id,
            order_id=order_id,
            payload=payload,
            created_by=current_user.id,
            vin=vin,
        )
        self._timeline.record(
            current_user,
            order_id,
            "VEHICLE_ADDED",
            "Vehicle added to order.",
        )
        self._audit.record_order_vehicle_added(
            company_id=current_user.company_id,
            user_id=current_user.id,
            entity_id=str(vehicle.id),
            ip_address=ip_address,
        )
        return vehicle

    def update_vehicle(
        self,
        current_user: User,
        vehicle_id: uuid.UUID,
        payload: OrderVehicleUpdateRequest,
        ip_address: str | None,
    ) -> OrderVehicle:
        """Update a vehicle."""
        vehicle = self._vehicles.get_by_id_for_company(vehicle_id, current_user.company_id)
        if vehicle is None:
            raise NotFoundError(code="VEHICLE_NOT_FOUND", message="Vehicle not found.")
        self._get_editable_order(current_user, vehicle.order_id)
        stops = self._stops.list_for_order(vehicle.order_id, current_user.company_id)
        validate_vehicle_stop_links(stops, payload)
        vin = normalize_vin(payload.vin) if payload.vin else vehicle.vin
        updated_vehicle = self._vehicles.update(
            vehicle,
            payload,
            current_user.id,
            vin=vin,
        )
        self._timeline.record(
            current_user,
            vehicle.order_id,
            "ORDER_UPDATED",
            "Vehicle details updated.",
        )
        self._audit.record_order_vehicle_updated(
            company_id=current_user.company_id,
            user_id=current_user.id,
            entity_id=str(updated_vehicle.id),
            ip_address=ip_address,
        )
        return updated_vehicle

    def delete_vehicle(
        self,
        current_user: User,
        vehicle_id: uuid.UUID,
        ip_address: str | None,
    ) -> None:
        """Soft delete a vehicle."""
        vehicle = self._vehicles.get_by_id_for_company(vehicle_id, current_user.company_id)
        if vehicle is None:
            raise NotFoundError(code="VEHICLE_NOT_FOUND", message="Vehicle not found.")
        self._get_editable_order(current_user, vehicle.order_id)
        self._vehicles.soft_delete(vehicle, current_user.id)
        self._timeline.record(
            current_user,
            vehicle.order_id,
            "VEHICLE_REMOVED",
            "Vehicle removed from order.",
        )
        self._audit.record_order_vehicle_removed(
            company_id=current_user.company_id,
            user_id=current_user.id,
            entity_id=str(vehicle.id),
            ip_address=ip_address,
        )

    def get_vehicle_for_company(
        self,
        vehicle_id: uuid.UUID,
        company_id: uuid.UUID,
    ) -> OrderVehicle | None:
        """Return a vehicle scoped to a company."""
        return self._vehicles.get_by_id_for_company(vehicle_id, company_id)

    def update_vin(
        self,
        vehicle: OrderVehicle,
        vin: str,
        updated_by: uuid.UUID,
    ) -> OrderVehicle:
        """Update a vehicle VIN."""
        return self._vehicles.update_vin(vehicle, vin, updated_by)
