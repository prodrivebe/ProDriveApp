"""Order business logic."""

import uuid

from sqlalchemy.orm import Session

from app.audit.service import AuditService
from app.common.enums import OrderStatus, UserRole
from app.common.exceptions import NotFoundError, ValidationError
from app.common.tenant import ensure_same_company
from app.companies.repository import CompanyRepository
from app.customers.repository import CustomerRepository
from app.drivers.models import Driver
from app.drivers.repository import DriverRepository
from app.notifications.service import NotificationService
from app.order_stops.repository import OrderStopRepository
from app.order_stops.service import OrderStopService
from app.order_stops.validators import validate_stop_sequences
from app.order_timeline.service import OrderTimelineService
from app.order_vehicles.repository import OrderVehicleRepository
from app.order_vehicles.service import OrderVehicleService
from app.orders.models import Order, OrderStop, OrderTimelineEntry, OrderVehicle
from app.orders.repository import OrderRepository
from app.orders.schemas import (
    AssignDriverRequest,
    OrderCreateRequest,
    OrderStopCreateRequest,
    OrderStopUpdateRequest,
    OrderSummaryResponse,
    OrderUpdateRequest,
    OrderVehicleCreateRequest,
    OrderVehicleUpdateRequest,
    VinUpdateRequest,
)
from app.orders.validators import (
    ensure_order_view_access,
    normalize_vin,
    validate_order_editable,
    validate_status_transition,
    validate_vehicle_stop_links,
)
from app.workflow.service import OrderWorkflowService
from app.trailers.repository import TrailerRepository
from app.trucks.repository import TruckRepository
from app.users.models import User

MAX_PAGE_SIZE = 100


class OrderService:
    """Order management and workflow."""

    def __init__(self, db: Session) -> None:
        self._db = db
        self._orders = OrderRepository(db)
        self._stops = OrderStopRepository(db)
        self._vehicles = OrderVehicleRepository(db)
        self._stop_service = OrderStopService(db)
        self._vehicle_service = OrderVehicleService(db)
        self._timeline_service = OrderTimelineService(db)
        self._customers = CustomerRepository(db)
        self._drivers = DriverRepository(db)
        self._trucks = TruckRepository(db)
        self._trailers = TrailerRepository(db)
        self._companies = CompanyRepository(db)
        self._audit = AuditService(db)
        self._notifications = NotificationService(db)
        self._workflow = OrderWorkflowService(db)

    def list_orders(
        self,
        current_user: User,
        *,
        page: int,
        page_size: int,
        status: OrderStatus | None,
        customer_id: uuid.UUID | None,
        driver_id: uuid.UUID | None,
        search: str | None,
    ) -> tuple[list[Order], int]:
        """List orders for the current company."""
        normalized_page = max(page, 1)
        normalized_page_size = min(max(page_size, 1), MAX_PAGE_SIZE)
        return self._orders.list_for_company(
            current_user.company_id,
            page=normalized_page,
            page_size=normalized_page_size,
            status=status,
            customer_id=customer_id,
            driver_id=driver_id,
            search=search,
        )

    def get_order(self, current_user: User, order_id: uuid.UUID) -> Order:
        """Return an order with nested stops and vehicles."""
        order = self._orders.get_by_id_for_company(
            order_id,
            current_user.company_id,
            with_details=True,
        )
        if order is None:
            raise NotFoundError(code="ORDER_NOT_FOUND", message="Order not found.")
        ensure_same_company(order.company_id, current_user)
        assigned_driver = self._get_assigned_driver(order)
        ensure_order_view_access(current_user, order, assigned_driver)
        order.stops = [
            stop
            for stop in order.stops
            if stop.deleted_at is None
        ]
        order.vehicles = [
            vehicle
            for vehicle in order.vehicles
            if vehicle.deleted_at is None
        ]
        order.stops.sort(key=lambda stop: stop.sequence)
        return order

    def _generate_order_number(self, company_id: uuid.UUID) -> str:
        settings = self._companies.get_settings_for_company(company_id)
        prefix = settings.order_number_prefix if settings else None
        normalized_prefix = prefix or "ORD-"
        sequence = self._orders.count_for_company(company_id) + 1
        return f"{normalized_prefix}{sequence:06d}"

    def _validate_customer(self, current_user: User, customer_id: uuid.UUID) -> None:
        customer = self._customers.get_by_id_for_company(customer_id, current_user.company_id)
        if customer is None:
            raise ValidationError(
                code="INVALID_CUSTOMER",
                message="Customer not found in this company.",
            )

    def create_order(
        self,
        current_user: User,
        payload: OrderCreateRequest,
        ip_address: str | None,
    ) -> Order:
        """Create an order with optional wizard stops and vehicles."""
        self._validate_customer(current_user, payload.customer_id)
        if payload.stops:
            validate_stop_sequences(payload.stops)

        order = self._orders.create(
            company_id=current_user.company_id,
            customer_id=payload.customer_id,
            order_number=self._generate_order_number(current_user.company_id),
            payload=payload,
            created_by=current_user.id,
        )
        created_stops: list[OrderStop] = []
        for stop_payload in payload.stops:
            stop = self._stops.create(
                company_id=current_user.company_id,
                order_id=order.id,
                payload=stop_payload,
                created_by=current_user.id,
            )
            created_stops.append(stop)
            self._record_timeline(
                current_user,
                order.id,
                "STOP_ADDED",
                f"{stop_payload.stop_type.value} stop added at sequence {stop_payload.sequence}.",
            )
            self._audit.record_order_stop_added(
                company_id=current_user.company_id,
                user_id=current_user.id,
                entity_id=str(stop.id),
                ip_address=ip_address,
            )

        for vehicle_payload in payload.vehicles:
            vin = (
                normalize_vin(vehicle_payload.vin) if vehicle_payload.vin else None
            )
            if created_stops:
                validate_vehicle_stop_links(created_stops, vehicle_payload)
            vehicle = self._vehicles.create(
                company_id=current_user.company_id,
                order_id=order.id,
                payload=vehicle_payload,
                created_by=current_user.id,
                vin=vin,
            )
            self._record_timeline(
                current_user,
                order.id,
                "VEHICLE_ADDED",
                "Vehicle added to order.",
            )
            self._audit.record_order_vehicle_added(
                company_id=current_user.company_id,
                user_id=current_user.id,
                entity_id=str(vehicle.id),
                ip_address=ip_address,
            )

        self._record_timeline(
            current_user,
            order.id,
            "ORDER_CREATED",
            f"Order {order.order_number} created.",
        )
        self._audit.record_order_created(
            company_id=current_user.company_id,
            user_id=current_user.id,
            entity_id=str(order.id),
            ip_address=ip_address,
        )
        return self.get_order(current_user, order.id)

    def update_order(
        self,
        current_user: User,
        order_id: uuid.UUID,
        payload: OrderUpdateRequest,
        ip_address: str | None,
    ) -> Order:
        """Update an order header."""
        order = self.get_order(current_user, order_id)
        validate_order_editable(order)
        self._validate_customer(current_user, payload.customer_id)
        status_changed = (
            payload.status is not None and payload.status != OrderStatus(order.status)
        )
        previous_status = OrderStatus(order.status)
        if status_changed and payload.status is not None:
            validate_status_transition(order, payload.status)
        updated_order = self._orders.update(order, payload, current_user.id)
        self._record_timeline(
            current_user,
            order.id,
            "ORDER_UPDATED",
            f"Order {order.order_number} updated.",
        )
        if status_changed and payload.status is not None:
            self._record_status_change(
                current_user,
                order.id,
                previous_status,
                payload.status,
                ip_address,
            )
        self._audit.record_order_updated(
            company_id=current_user.company_id,
            user_id=current_user.id,
            entity_id=str(order.id),
            ip_address=ip_address,
        )
        return self.get_order(current_user, updated_order.id)

    def delete_order(
        self,
        current_user: User,
        order_id: uuid.UUID,
        ip_address: str | None,
    ) -> None:
        """Soft delete an order."""
        order = self.get_order(current_user, order_id)
        validate_order_editable(order)
        self._orders.soft_delete(order, current_user.id)
        self._record_timeline(
            current_user,
            order.id,
            "ORDER_DELETED",
            f"Order {order.order_number} deleted.",
        )
        self._audit.record_order_deleted(
            company_id=current_user.company_id,
            user_id=current_user.id,
            entity_id=str(order.id),
            ip_address=ip_address,
        )

    def list_stops(self, current_user: User, order_id: uuid.UUID) -> list[OrderStop]:
        """List stops for an order."""
        self.get_order(current_user, order_id)
        return self._stop_service.list_stops(current_user, order_id)

    def create_stop(
        self,
        current_user: User,
        order_id: uuid.UUID,
        payload: OrderStopCreateRequest,
        ip_address: str | None = None,
    ) -> OrderStop:
        """Create a stop on an order."""
        return self._stop_service.create_stop(
            current_user,
            order_id,
            payload,
            ip_address,
        )

    def update_stop(
        self,
        current_user: User,
        stop_id: uuid.UUID,
        payload: OrderStopUpdateRequest,
        ip_address: str | None = None,
    ) -> OrderStop:
        """Update a stop."""
        return self._stop_service.update_stop(
            current_user,
            stop_id,
            payload,
            ip_address,
        )

    def delete_stop(
        self,
        current_user: User,
        stop_id: uuid.UUID,
        ip_address: str | None = None,
    ) -> None:
        """Soft delete a stop."""
        self._stop_service.delete_stop(current_user, stop_id, ip_address)

    def list_vehicles(self, current_user: User, order_id: uuid.UUID) -> list[OrderVehicle]:
        """List vehicles for an order."""
        self.get_order(current_user, order_id)
        return self._vehicle_service.list_vehicles(current_user, order_id)

    def create_vehicle(
        self,
        current_user: User,
        order_id: uuid.UUID,
        payload: OrderVehicleCreateRequest,
        ip_address: str | None = None,
    ) -> OrderVehicle:
        """Create a vehicle on an order."""
        return self._vehicle_service.create_vehicle(
            current_user,
            order_id,
            payload,
            ip_address,
        )

    def update_vehicle(
        self,
        current_user: User,
        vehicle_id: uuid.UUID,
        payload: OrderVehicleUpdateRequest,
        ip_address: str | None = None,
    ) -> OrderVehicle:
        """Update a vehicle."""
        return self._vehicle_service.update_vehicle(
            current_user,
            vehicle_id,
            payload,
            ip_address,
        )

    def delete_vehicle(
        self,
        current_user: User,
        vehicle_id: uuid.UUID,
        ip_address: str | None = None,
    ) -> None:
        """Soft delete a vehicle."""
        self._vehicle_service.delete_vehicle(current_user, vehicle_id, ip_address)

    def scan_vin(
        self,
        current_user: User,
        vehicle_id: uuid.UUID,
        payload: VinUpdateRequest,
        ip_address: str | None,
    ) -> OrderVehicle:
        """Scan and store a vehicle VIN."""
        return self._update_vehicle_vin(
            current_user,
            vehicle_id,
            payload,
            ip_address=ip_address,
            action="VIN_SCANNED",
            audit_method="record_vehicle_vin_scanned",
        )

    def update_vin(
        self,
        current_user: User,
        vehicle_id: uuid.UUID,
        payload: VinUpdateRequest,
        ip_address: str | None,
    ) -> OrderVehicle:
        """Manually update a vehicle VIN."""
        return self._update_vehicle_vin(
            current_user,
            vehicle_id,
            payload,
            ip_address=ip_address,
            action="VIN_UPDATED",
            audit_method="record_vehicle_vin_updated",
        )

    def assign_driver(
        self,
        current_user: User,
        order_id: uuid.UUID,
        payload: AssignDriverRequest,
        ip_address: str | None,
    ) -> Order:
        """Assign fleet resources to an order."""
        order = self.get_order(current_user, order_id)
        validate_order_editable(order)
        validate_status_transition(order, OrderStatus.ASSIGNED)

        driver = self._drivers.get_by_id_for_company(payload.driver_id, current_user.company_id)
        if driver is None or not driver.active:
            raise ValidationError(code="INVALID_DRIVER", message="Driver not found or inactive.")

        if payload.truck_id is not None:
            truck = self._trucks.get_by_id_for_company(payload.truck_id, current_user.company_id)
            if truck is None or not truck.active:
                raise ValidationError(code="INVALID_TRUCK", message="Truck not found or inactive.")

        if payload.trailer_id is not None:
            trailer = self._trailers.get_by_id_for_company(
                payload.trailer_id,
                current_user.company_id,
            )
            if trailer is None or not trailer.active:
                raise ValidationError(
                    code="INVALID_TRAILER",
                    message="Trailer not found or inactive.",
                )

        previous_status = OrderStatus(order.status)
        updated_order = self._orders.update_status(
            order,
            OrderStatus.ASSIGNED,
            current_user.id,
            assigned_driver_id=payload.driver_id,
            assigned_truck_id=payload.truck_id,
            assigned_trailer_id=payload.trailer_id,
        )
        self._record_timeline(
            current_user,
            order_id,
            "DRIVER_ASSIGNED",
            "Driver assigned to order.",
        )
        self._record_status_change(
            current_user,
            order_id,
            previous_status,
            OrderStatus.ASSIGNED,
            ip_address,
        )
        self._audit.record_order_driver_assigned(
            company_id=current_user.company_id,
            user_id=current_user.id,
            entity_id=str(order.id),
            ip_address=ip_address,
        )
        if driver.user_id is not None:
            self._notifications.notify_user(
                company_id=current_user.company_id,
                user_id=driver.user_id,
                title="New order assignment",
                message=f"Order {order.order_number} has been assigned to you.",
                notification_type="ORDER_ASSIGNED",
            )
        return self.get_order(current_user, updated_order.id)

    def accept_order(
        self,
        current_user: User,
        order_id: uuid.UUID,
        ip_address: str | None = None,
    ) -> Order:
        """Driver accepts an assigned order."""
        return self._workflow.accept_order(current_user, order_id, ip_address)

    def reject_order(
        self,
        current_user: User,
        order_id: uuid.UUID,
        ip_address: str | None = None,
    ) -> Order:
        """Driver rejects an assigned order."""
        return self._workflow.reject_order(current_user, order_id, ip_address)

    def arrive_pickup(
        self,
        current_user: User,
        order_id: uuid.UUID,
        ip_address: str | None = None,
    ) -> Order:
        """Mark arrival at pickup."""
        return self._workflow.arrive_pickup(current_user, order_id, ip_address)

    def start_loading(
        self,
        current_user: User,
        order_id: uuid.UUID,
        ip_address: str | None = None,
    ) -> Order:
        """Start loading at pickup."""
        return self._workflow.start_loading(current_user, order_id, ip_address)

    def complete_loading(
        self,
        current_user: User,
        order_id: uuid.UUID,
        ip_address: str | None = None,
    ) -> Order:
        """Mark loading complete."""
        return self._workflow.complete_loading(current_user, order_id, ip_address)

    def start_transit(
        self,
        current_user: User,
        order_id: uuid.UUID,
        ip_address: str | None = None,
    ) -> Order:
        """Start transit toward delivery."""
        return self._workflow.start_transit(current_user, order_id, ip_address)

    def arrive_delivery(
        self,
        current_user: User,
        order_id: uuid.UUID,
        ip_address: str | None = None,
    ) -> Order:
        """Mark arrival at delivery."""
        return self._workflow.arrive_delivery(current_user, order_id, ip_address)

    def start_delivery(
        self,
        current_user: User,
        order_id: uuid.UUID,
        ip_address: str | None = None,
    ) -> Order:
        """Start delivery at the current stop."""
        return self._workflow.start_delivery(current_user, order_id, ip_address)

    def complete_delivery(
        self,
        current_user: User,
        order_id: uuid.UUID,
        ip_address: str | None = None,
    ) -> Order:
        """Mark delivery complete."""
        return self._workflow.complete_delivery(current_user, order_id, ip_address)

    def cancel_order(
        self,
        current_user: User,
        order_id: uuid.UUID,
        ip_address: str | None,
    ) -> Order:
        """Cancel an order."""
        order = self.get_order(current_user, order_id)
        validate_status_transition(order, OrderStatus.CANCELLED)
        previous_status = OrderStatus(order.status)
        updated_order = self._orders.update_status(
            order,
            OrderStatus.CANCELLED,
            current_user.id,
        )
        self._record_timeline(
            current_user,
            order_id,
            "ORDER_CANCELLED",
            f"Order {order.order_number} cancelled.",
        )
        self._record_status_change(
            current_user,
            order_id,
            previous_status,
            OrderStatus.CANCELLED,
            ip_address,
        )
        self._audit.record_order_cancelled(
            company_id=current_user.company_id,
            user_id=current_user.id,
            entity_id=str(order.id),
            ip_address=ip_address,
        )
        return self.get_order(current_user, updated_order.id)

    def list_timeline(
        self,
        current_user: User,
        order_id: uuid.UUID,
    ) -> list[OrderTimelineEntry]:
        """Return timeline entries for an order."""
        self.get_order(current_user, order_id)
        return self._timeline_service.list_for_order(current_user, order_id)

    def list_orders_for_customer(
        self,
        current_user: User,
        customer_id: uuid.UUID,
    ) -> list[OrderSummaryResponse]:
        """Return order summaries for customer history."""
        orders, _ = self._orders.list_for_company(
            current_user.company_id,
            page=1,
            page_size=MAX_PAGE_SIZE,
            customer_id=customer_id,
        )
        return [
            OrderSummaryResponse(
                id=order.id,
                order_number=order.order_number,
                status=OrderStatus(order.status),
                customer_id=order.customer_id,
                planned_pickup_date=order.planned_pickup_date,
                planned_delivery_date=order.planned_delivery_date,
                created_at=order.created_at,
            )
            for order in orders
        ]

    def list_orders_for_driver(
        self,
        current_user: User,
        driver_id: uuid.UUID,
    ) -> list[OrderSummaryResponse]:
        """Return order summaries assigned to a driver."""
        orders, _ = self._orders.list_for_company(
            current_user.company_id,
            page=1,
            page_size=MAX_PAGE_SIZE,
            driver_id=driver_id,
        )
        return [
            OrderSummaryResponse(
                id=order.id,
                order_number=order.order_number,
                status=OrderStatus(order.status),
                customer_id=order.customer_id,
                planned_pickup_date=order.planned_pickup_date,
                planned_delivery_date=order.planned_delivery_date,
                created_at=order.created_at,
            )
            for order in orders
        ]

    def _get_assigned_driver(self, order: Order) -> Driver | None:
        if order.assigned_driver_id is None:
            return None
        return self._drivers.get_by_id_for_company(
            order.assigned_driver_id,
            order.company_id,
        )

    def _update_vehicle_vin(
        self,
        current_user: User,
        vehicle_id: uuid.UUID,
        payload: VinUpdateRequest,
        *,
        ip_address: str | None,
        action: str,
        audit_method: str,
    ) -> OrderVehicle:
        vehicle = self._vehicle_service.get_vehicle_for_company(
            vehicle_id,
            current_user.company_id,
        )
        if vehicle is None:
            raise NotFoundError(code="VEHICLE_NOT_FOUND", message="Vehicle not found.")
        order = self.get_order(current_user, vehicle.order_id)
        validate_order_editable(order)
        normalized_vin = normalize_vin(payload.vin)
        old_vin = vehicle.vin
        updated_vehicle = self._vehicle_service.update_vin(
            vehicle,
            normalized_vin,
            current_user.id,
        )
        self._record_timeline(
            current_user,
            vehicle.order_id,
            action,
            f"Vehicle VIN updated to {normalized_vin}.",
        )
        audit_fn = getattr(self._audit, audit_method)
        audit_fn(
            company_id=current_user.company_id,
            user_id=current_user.id,
            entity_id=str(vehicle.id),
            old_value=old_vin,
            new_value=normalized_vin,
            ip_address=ip_address,
        )
        return updated_vehicle

    def _record_status_change(
        self,
        current_user: User,
        order_id: uuid.UUID,
        previous_status: OrderStatus,
        target_status: OrderStatus,
        ip_address: str | None,
    ) -> None:
        self._record_timeline(
            current_user,
            order_id,
            "STATUS_CHANGED",
            f"Order status changed from {previous_status.value} to {target_status.value}.",
        )
        self._audit.record_order_status_changed(
            company_id=current_user.company_id,
            user_id=current_user.id,
            entity_id=str(order_id),
            old_value=previous_status.value,
            new_value=target_status.value,
            ip_address=ip_address,
        )

    def _record_timeline(
        self,
        current_user: User,
        order_id: uuid.UUID,
        event_type: str,
        description: str,
    ) -> None:
        self.record_timeline_event(current_user, order_id, event_type, description)

    def record_timeline_event(
        self,
        current_user: User,
        order_id: uuid.UUID,
        event_type: str,
        description: str,
    ) -> None:
        """Record an order timeline event."""
        self._timeline_service.record(
            current_user,
            order_id,
            event_type,
            description,
        )

