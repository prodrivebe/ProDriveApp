"""Driver operational workflow business logic."""

import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.audit.service import AuditService
from app.common.enums import OrderStatus, StopProgressStatus, StopType, UserRole
from app.common.exceptions import NotFoundError, ValidationError
from app.drivers.models import Driver
from app.drivers.repository import DriverRepository
from app.notifications.service import NotificationService
from app.order_stops.repository import OrderStopRepository
from app.order_timeline.service import OrderTimelineService
from app.orders.models import Order, OrderStop
from app.orders.repository import OrderRepository
from app.orders.validators import ensure_workflow_actor
from app.order_stops.schemas import OrderStopResponse
from app.order_vehicles.schemas import OrderVehicleResponse
from app.orders.schemas import OrderResponse
from app.users.models import User
from app.workflow.schemas import DriverCurrentOrderResponse
from app.workflow.validators import (
    ACTIVE_WORKFLOW_STATUSES,
    NEXT_REQUIRED_ACTIONS,
    all_deliveries_completed,
    all_pickups_completed,
    get_current_stop,
    get_remaining_stops,
    validate_current_stop_type,
    validate_order_in_workflow,
    validate_status_transition,
    validate_stop_progress_transition,
)


class OrderWorkflowService:
    """Driver order execution state machine."""

    def __init__(self, db: Session) -> None:
        self._db = db
        self._orders = OrderRepository(db)
        self._stops = OrderStopRepository(db)
        self._drivers = DriverRepository(db)
        self._timeline = OrderTimelineService(db)
        self._audit = AuditService(db)
        self._notifications = NotificationService(db)

    def get_driver_current_order(self, current_user: User) -> DriverCurrentOrderResponse:
        """Return the active order context for the driver home screen."""
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
            raise NotFoundError(code="DRIVER_NOT_FOUND", message="Driver profile not found.")

        orders, _ = self._orders.list_for_company(
            current_user.company_id,
            page=1,
            page_size=100,
            driver_id=driver.id,
        )
        active_orders = [
            order
            for order in orders
            if OrderStatus(order.status) in ACTIVE_WORKFLOW_STATUSES
        ]
        if not active_orders:
            return DriverCurrentOrderResponse()

        order = sorted(active_orders, key=lambda item: item.created_at)[0]
        detailed = self._orders.get_by_id_for_company(
            order.id,
            current_user.company_id,
            with_details=True,
        )
        if detailed is None:
            raise NotFoundError(code="ORDER_NOT_FOUND", message="Order not found.")

        stops = [stop for stop in detailed.stops if stop.deleted_at is None]
        stops.sort(key=lambda item: item.sequence)
        vehicles = [vehicle for vehicle in detailed.vehicles if vehicle.deleted_at is None]
        current_stop = get_current_stop(stops)
        remaining_stops = get_remaining_stops(stops, current_stop)
        workflow_status = OrderStatus(detailed.status)

        return DriverCurrentOrderResponse(
            order=OrderResponse.model_validate(detailed),
            current_stop=(
                OrderStopResponse.model_validate(current_stop)
                if current_stop is not None
                else None
            ),
            remaining_stops=[
                OrderStopResponse.model_validate(stop) for stop in remaining_stops
            ],
            vehicles=[OrderVehicleResponse.model_validate(vehicle) for vehicle in vehicles],
            next_required_action=NEXT_REQUIRED_ACTIONS.get(
                workflow_status,
                "Review order details",
            ),
            workflow_status=workflow_status,
        )

    def accept_order(
        self,
        current_user: User,
        order_id: uuid.UUID,
        ip_address: str | None = None,
    ) -> Order:
        """Driver accepts an assigned order."""
        order = self._get_workflow_order(current_user, order_id)
        return self._transition(
            current_user,
            order,
            target_status=OrderStatus.ACCEPTED,
            event_type="DRIVER_ACCEPTED",
            description="Driver accepted the order.",
            ip_address=ip_address,
            notify_staff_type="ORDER_ACCEPTED",
            notify_staff_title="Order accepted",
            notify_staff_message=f"Order {order.order_number} was accepted by the driver.",
        )

    def reject_order(
        self,
        current_user: User,
        order_id: uuid.UUID,
        ip_address: str | None = None,
    ) -> Order:
        """Driver rejects an assigned order."""
        order = self._get_workflow_order(current_user, order_id)
        driver = self._get_assigned_driver(order)
        ensure_workflow_actor(current_user, order, driver)
        validate_status_transition(order, OrderStatus.READY)
        previous_status = OrderStatus(order.status)
        updated_order = self._orders.update_status(
            order,
            OrderStatus.READY,
            current_user.id,
            clear_assignment=True,
        )
        self._record_workflow_event(
            current_user,
            order.id,
            previous_status,
            OrderStatus.READY,
            event_type="DRIVER_REJECTED",
            description="Driver rejected the assignment.",
            ip_address=ip_address,
        )
        self._notifications.notify_staff(
            company_id=current_user.company_id,
            roles={UserRole.ADMIN, UserRole.DISPATCHER},
            title="Order rejected",
            message=f"Order {order.order_number} was rejected by the driver.",
            notification_type="ORDER_REJECTED",
        )
        return self._reload_order(current_user, updated_order.id)

    def arrive_pickup(
        self,
        current_user: User,
        order_id: uuid.UUID,
        ip_address: str | None = None,
    ) -> Order:
        """Mark arrival at the current pickup stop."""
        order = self._get_workflow_order(current_user, order_id)
        stops = self._stops.list_for_order(order.id, current_user.company_id)
        current_stop = get_current_stop(stops)
        validate_current_stop_type(current_stop, StopType.PICKUP)
        if current_stop is not None:
            self._advance_stop_progress(
                current_stop,
                StopProgressStatus.ARRIVED,
                current_user.id,
            )
        return self._transition(
            current_user,
            order,
            target_status=OrderStatus.ARRIVED_PICKUP,
            event_type="ARRIVED_PICKUP",
            description="Driver arrived at pickup.",
            ip_address=ip_address,
            notify_staff_type="PICKUP_ARRIVED",
            notify_staff_title="Pickup arrival",
            notify_staff_message=f"Driver arrived at pickup for order {order.order_number}.",
        )

    def start_loading(
        self,
        current_user: User,
        order_id: uuid.UUID,
        ip_address: str | None = None,
    ) -> Order:
        """Start loading at the current pickup stop."""
        order = self._get_workflow_order(current_user, order_id)
        stops = self._stops.list_for_order(order.id, current_user.company_id)
        current_stop = get_current_stop(stops)
        validate_current_stop_type(current_stop, StopType.PICKUP)
        if current_stop is not None:
            self._advance_stop_progress(
                current_stop,
                StopProgressStatus.LOADING,
                current_user.id,
            )
        return self._transition(
            current_user,
            order,
            target_status=OrderStatus.LOADING,
            event_type="LOADING_STARTED",
            description="Loading started.",
            ip_address=ip_address,
        )

    def complete_loading(
        self,
        current_user: User,
        order_id: uuid.UUID,
        ip_address: str | None = None,
    ) -> Order:
        """Complete loading at the current pickup stop."""
        order = self._get_workflow_order(current_user, order_id)
        stops = self._stops.list_for_order(order.id, current_user.company_id)
        current_stop = get_current_stop(stops)
        validate_current_stop_type(current_stop, StopType.PICKUP)
        if current_stop is not None:
            self._advance_stop_progress(
                current_stop,
                StopProgressStatus.COMPLETED,
                current_user.id,
            )
            stops = self._stops.list_for_order(order.id, current_user.company_id)

        target_status = (
            OrderStatus.LOADED
            if all_pickups_completed(stops)
            else OrderStatus.ACCEPTED
        )
        description = (
            "Loading completed."
            if target_status == OrderStatus.LOADED
            else "Pickup stop completed. Proceed to the next pickup."
        )
        return self._transition(
            current_user,
            order,
            target_status=target_status,
            event_type="LOADING_COMPLETE",
            description=description,
            ip_address=ip_address,
            notify_staff_type="LOADING_COMPLETED",
            notify_staff_title="Loading completed",
            notify_staff_message=f"Loading completed for order {order.order_number}.",
            notify_only_when=target_status == OrderStatus.LOADED,
        )

    def start_transit(
        self,
        current_user: User,
        order_id: uuid.UUID,
        ip_address: str | None = None,
    ) -> Order:
        """Start transit toward delivery."""
        order = self._get_workflow_order(current_user, order_id)
        stops = self._stops.list_for_order(order.id, current_user.company_id)
        if stops and not all_pickups_completed(stops):
            raise ValidationError(
                code="PICKUPS_INCOMPLETE",
                message="All pickup stops must be completed before starting transit.",
            )
        return self._transition(
            current_user,
            order,
            target_status=OrderStatus.IN_TRANSIT,
            event_type="TRANSIT_STARTED",
            description="Transit started.",
            ip_address=ip_address,
        )

    def arrive_delivery(
        self,
        current_user: User,
        order_id: uuid.UUID,
        ip_address: str | None = None,
    ) -> Order:
        """Mark arrival at the current delivery stop."""
        order = self._get_workflow_order(current_user, order_id)
        stops = self._stops.list_for_order(order.id, current_user.company_id)
        current_stop = get_current_stop(stops)
        validate_current_stop_type(current_stop, StopType.DELIVERY)
        if current_stop is not None:
            self._advance_stop_progress(
                current_stop,
                StopProgressStatus.ARRIVED,
                current_user.id,
            )
        return self._transition(
            current_user,
            order,
            target_status=OrderStatus.ARRIVED_DELIVERY,
            event_type="ARRIVED_DELIVERY",
            description="Driver arrived at delivery.",
            ip_address=ip_address,
            notify_staff_type="DELIVERY_ARRIVED",
            notify_staff_title="Delivery arrival",
            notify_staff_message=f"Driver arrived at delivery for order {order.order_number}.",
        )

    def start_delivery(
        self,
        current_user: User,
        order_id: uuid.UUID,
        ip_address: str | None = None,
    ) -> Order:
        """Start delivery/unloading at the current delivery stop."""
        order = self._get_workflow_order(current_user, order_id)
        stops = self._stops.list_for_order(order.id, current_user.company_id)
        current_stop = get_current_stop(stops)
        validate_current_stop_type(current_stop, StopType.DELIVERY)
        if current_stop is not None:
            self._advance_stop_progress(
                current_stop,
                StopProgressStatus.LOADING,
                current_user.id,
            )
        return self._transition(
            current_user,
            order,
            target_status=OrderStatus.DELIVERING,
            event_type="DELIVERY_STARTED",
            description="Delivery started.",
            ip_address=ip_address,
        )

    def complete_delivery(
        self,
        current_user: User,
        order_id: uuid.UUID,
        ip_address: str | None = None,
    ) -> Order:
        """Complete delivery at the current delivery stop."""
        order = self._get_workflow_order(current_user, order_id)
        stops = self._stops.list_for_order(order.id, current_user.company_id)
        current_stop = get_current_stop(stops)
        validate_current_stop_type(current_stop, StopType.DELIVERY)
        if current_stop is not None:
            self._advance_stop_progress(
                current_stop,
                StopProgressStatus.COMPLETED,
                current_user.id,
            )
            stops = self._stops.list_for_order(order.id, current_user.company_id)

        target_status = (
            OrderStatus.COMPLETED
            if all_deliveries_completed(stops)
            else OrderStatus.IN_TRANSIT
        )
        description = (
            "Order completed."
            if target_status == OrderStatus.COMPLETED
            else "Delivery stop completed. Proceed to the next delivery."
        )
        updated = self._transition(
            current_user,
            order,
            target_status=target_status,
            event_type="DELIVERY_COMPLETE",
            description=description,
            ip_address=ip_address,
            notify_staff_type="ORDER_COMPLETED",
            notify_staff_title="Order completed",
            notify_staff_message=f"Order {order.order_number} has been delivered.",
            notify_only_when=target_status == OrderStatus.COMPLETED,
        )
        return updated

    def _get_workflow_order(self, current_user: User, order_id: uuid.UUID) -> Order:
        order = self._orders.get_by_id_for_company(
            order_id,
            current_user.company_id,
            with_details=False,
        )
        if order is None:
            raise NotFoundError(code="ORDER_NOT_FOUND", message="Order not found.")
        validate_order_in_workflow(order)
        driver = self._get_assigned_driver(order)
        ensure_workflow_actor(current_user, order, driver)
        return order

    def _get_assigned_driver(self, order: Order) -> Driver | None:
        if order.assigned_driver_id is None:
            return None
        return self._drivers.get_by_id_for_company(
            order.assigned_driver_id,
            order.company_id,
        )

    def _advance_stop_progress(
        self,
        stop: OrderStop,
        target_status: StopProgressStatus,
        updated_by: uuid.UUID,
    ) -> OrderStop:
        validate_stop_progress_transition(stop, target_status)
        return self._stops.update_progress(stop, target_status, updated_by)

    def _transition(
        self,
        current_user: User,
        order: Order,
        *,
        target_status: OrderStatus,
        event_type: str,
        description: str,
        ip_address: str | None,
        notify_staff_type: str | None = None,
        notify_staff_title: str | None = None,
        notify_staff_message: str | None = None,
        notify_only_when: bool = True,
    ) -> Order:
        previous_status = OrderStatus(order.status)
        validate_status_transition(order, target_status)
        updated_order = self._orders.update_status(order, target_status, current_user.id)
        self._record_workflow_event(
            current_user,
            order.id,
            previous_status,
            target_status,
            event_type=event_type,
            description=description,
            ip_address=ip_address,
        )
        if (
            notify_staff_type
            and notify_staff_title
            and notify_staff_message
            and notify_only_when
        ):
            self._notifications.notify_staff(
                company_id=current_user.company_id,
                roles={UserRole.ADMIN, UserRole.DISPATCHER},
                title=notify_staff_title,
                message=notify_staff_message,
                notification_type=notify_staff_type,
            )
        return self._reload_order(current_user, updated_order.id)

    def _record_workflow_event(
        self,
        current_user: User,
        order_id: uuid.UUID,
        previous_status: OrderStatus,
        new_status: OrderStatus,
        *,
        event_type: str,
        description: str,
        ip_address: str | None,
    ) -> None:
        self._timeline.record(current_user, order_id, event_type, description)
        if new_status != previous_status:
            self._timeline.record(
                current_user,
                order_id,
                "STATUS_CHANGED",
                f"Order status changed from {previous_status.value} to {new_status.value}.",
            )
        self._audit.record_order_workflow_transition(
            company_id=current_user.company_id,
            user_id=current_user.id,
            entity_id=str(order_id),
            old_value=previous_status.value,
            new_value=new_status.value,
            action=event_type,
            ip_address=ip_address,
        )

    def _reload_order(self, current_user: User, order_id: uuid.UUID) -> Order:
        order = self._orders.get_by_id_for_company(
            order_id,
            current_user.company_id,
            with_details=True,
        )
        if order is None:
            raise NotFoundError(code="ORDER_NOT_FOUND", message="Order not found.")
        order.stops = [stop for stop in order.stops if stop.deleted_at is None]
        order.vehicles = [vehicle for vehicle in order.vehicles if vehicle.deleted_at is None]
        order.stops.sort(key=lambda stop: stop.sequence)
        return order
