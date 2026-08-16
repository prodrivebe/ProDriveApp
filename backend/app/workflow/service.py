"""Driver operational workflow business logic."""

import logging
import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.audit.service import AuditService
from app.common.enums import OrderDocumentType, OrderStatus, StopProgressStatus, StopType, UserRole
from app.common.exceptions import AuthorizationError, NotFoundError, ValidationError
from app.drivers.models import Driver
from app.drivers.repository import DriverRepository
from app.notifications.service import NotificationService
from app.order_documents.repository import OrderDocumentRepository
from app.order_stops.repository import OrderStopRepository
from app.order_timeline.service import OrderTimelineService
from app.order_vehicles.repository import OrderVehicleRepository
from app.orders.models import Order, OrderStop
from app.orders.repository import OrderRepository
from app.orders.validators import ensure_workflow_actor
from app.order_stops.schemas import OrderStopResponse
from app.order_vehicles.schemas import OrderVehicleResponse
from app.orders.schemas import OrderResponse
from app.users.models import User
from app.realtime.publisher import publish_order_event
from app.realtime.schemas import RealtimeEventType
from app.realtime.workflow_events import WORKFLOW_REALTIME_EVENTS
from app.workflow.schemas import DriverCurrentOrderResponse
from app.workflow.validators import (
    ACTIVE_WORKFLOW_STATUSES,
    NEXT_REQUIRED_ACTIONS,
    all_deliveries_completed,
    all_pickups_completed,
    get_active_stops,
    get_current_stop,
    get_delivery_stop,
    get_pickup_stop,
    get_remaining_stops,
    ensure_driver_forward_transition,
    validate_current_stop_type,
    validate_order_in_workflow,
    validate_status_transition,
    validate_stop_progress_transition,
)


logger = logging.getLogger(__name__)


class OrderWorkflowService:
    """Driver order execution state machine."""

    def __init__(self, db: Session) -> None:
        self._db = db
        self._orders = OrderRepository(db)
        self._stops = OrderStopRepository(db)
        self._documents = OrderDocumentRepository(db)
        self._vehicles = OrderVehicleRepository(db)
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

        stops = get_active_stops([stop for stop in detailed.stops if stop.deleted_at is None])
        vehicles = [vehicle for vehicle in detailed.vehicles if vehicle.deleted_at is None]
        workflow_status = OrderStatus(detailed.status)
        current_stop = get_current_stop(stops, workflow_status)
        remaining_stops = get_remaining_stops(stops, current_stop)

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
            order_id=order.id,
        )
        reloaded = self._reload_order(current_user, updated_order.id)
        driver = self._get_assigned_driver(order)
        publish_order_event(
            company_id=current_user.company_id,
            order_id=order.id,
            event_type=RealtimeEventType.ORDER_REJECTED,
            order_number=order.order_number,
            status=OrderStatus.READY.value,
            driver_user_id=driver.user_id if driver is not None else None,
        )
        return reloaded

    def arrive_pickup(
        self,
        current_user: User,
        order_id: uuid.UUID,
        ip_address: str | None = None,
    ) -> Order:
        """Mark arrival at the current pickup stop."""
        order = self._get_workflow_order(current_user, order_id)
        stops = get_active_stops(
            self._stops.list_for_order(order.id, current_user.company_id)
        )
        pickup_stop = get_pickup_stop(stops)
        logger.info(
            "Workflow arrive_pickup order_id=%s current_status=%s pickup_stop=%s pickup_progress=%s",
            order.id,
            order.status,
            pickup_stop.id if pickup_stop is not None else None,
            pickup_stop.progress_status if pickup_stop is not None else None,
        )
        validate_current_stop_type(pickup_stop, StopType.PICKUP)
        if pickup_stop is not None:
            self._advance_stop_progress(
                pickup_stop,
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
        current_status = OrderStatus(order.status)
        logger.info(
            "Workflow start_loading begin order_id=%s current_status=%s user_id=%s",
            order.id,
            current_status.value,
            current_user.id,
        )
        validate_status_transition(order, OrderStatus.LOADING)
        logger.info(
            "Workflow start_loading validation passed order_id=%s %s -> LOADING",
            order.id,
            current_status.value,
        )

        stops = get_active_stops(
            self._stops.list_for_order(order.id, current_user.company_id)
        )
        pickup_stop = get_pickup_stop(stops)
        logger.info(
            "Workflow start_loading pickup_stop order_id=%s stop_id=%s progress=%s",
            order.id,
            pickup_stop.id if pickup_stop is not None else None,
            pickup_stop.progress_status if pickup_stop is not None else None,
        )
        validate_current_stop_type(pickup_stop, StopType.PICKUP)
        if pickup_stop is not None:
            self._prepare_pickup_stop_for_loading(pickup_stop, current_user.id)

        updated = self._transition(
            current_user,
            order,
            target_status=OrderStatus.LOADING,
            event_type="LOADING_STARTED",
            description="Loading started.",
            ip_address=ip_address,
            notify_staff_type="LOADING_STARTED",
            notify_staff_title="Loading started",
            notify_staff_message=f"Driver started loading for order {order.order_number}.",
        )
        logger.info(
            "Workflow start_loading complete order_id=%s response_status=%s",
            updated.id,
            updated.status,
        )
        return updated

    def complete_loading(
        self,
        current_user: User,
        order_id: uuid.UUID,
        ip_address: str | None = None,
    ) -> Order:
        """Complete loading at the current pickup stop."""
        from app.cmr.service import CmrService
        from app.config.settings import get_settings

        order = self._get_workflow_order(current_user, order_id)
        CmrService(self._db, get_settings()).ensure_cmr_generated(
            current_user,
            order_id,
        )
        self._validate_loading_vehicles_ready(order.id, current_user.company_id)
        stops = self._stops.list_for_order(order.id, current_user.company_id)
        current_stop = get_current_stop(stops, OrderStatus(order.status))
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

    def reopen_loading(
        self,
        current_user: User,
        order_id: uuid.UUID,
        reason: str,
        ip_address: str | None = None,
    ) -> Order:
        """Allow a dispatcher to reopen loading so vehicles can be edited again."""
        if current_user.role not in {UserRole.ADMIN, UserRole.DISPATCHER}:
            raise AuthorizationError(
                code="FORBIDDEN",
                message="Only dispatchers can reopen loading.",
            )

        order = self._orders.get_by_id_for_company(
            order_id,
            current_user.company_id,
            with_details=False,
        )
        if order is None:
            raise NotFoundError(code="ORDER_NOT_FOUND", message="Order not found.")

        validate_order_in_workflow(order)
        current_status = OrderStatus(order.status)
        if current_status != OrderStatus.LOADED:
            raise ValidationError(
                code="INVALID_ORDER_STATUS",
                message="Loading can only be reopened before transit starts.",
            )

        trimmed_reason = reason.strip()

        stops = get_active_stops(
            self._stops.list_for_order(order.id, current_user.company_id)
        )
        pickup_stop = get_pickup_stop(stops, require_incomplete=False)
        if pickup_stop is not None:
            if StopProgressStatus(pickup_stop.progress_status) == StopProgressStatus.COMPLETED:
                self._stops.update_progress(
                    pickup_stop,
                    StopProgressStatus.LOADING,
                    current_user.id,
                )

        previous_status = current_status
        updated_order = self._orders.update_status(
            order,
            OrderStatus.LOADING,
            current_user.id,
        )
        description = (
            f"Loading reopened by dispatcher: {trimmed_reason}"
            if trimmed_reason
            else "Loading reopened by dispatcher."
        )
        self._timeline.record(
            current_user,
            order.id,
            "LOADING_REOPENED",
            description,
        )
        self._audit.record_loading_reopened(
            company_id=current_user.company_id,
            user_id=current_user.id,
            entity_id=str(order.id),
            old_value=previous_status.value,
            new_value=OrderStatus.LOADING.value,
            reason=trimmed_reason or None,
            ip_address=ip_address,
        )
        self._notifications.notify_staff(
            company_id=current_user.company_id,
            roles={UserRole.ADMIN, UserRole.DISPATCHER},
            title="Loading reopened",
            message=f"Loading was reopened for order {order.order_number}.",
            notification_type="LOADING_REOPENED",
            order_id=order.id,
        )
        driver = self._get_assigned_driver(updated_order)
        if driver is not None:
            self._notifications.notify_user(
                company_id=current_user.company_id,
                user_id=driver.user_id,
                title="Loading reopened",
                message=(
                    f"Dispatcher reopened loading for order {order.order_number}. "
                    "You can edit vehicles again."
                ),
                notification_type="LOADING_REOPENED",
                order_id=order.id,
            )

        reloaded = self._reload_order(current_user, updated_order.id)
        publish_order_event(
            company_id=current_user.company_id,
            order_id=reloaded.id,
            event_type=RealtimeEventType.ORDER_UPDATED,
            order_number=reloaded.order_number,
            status=OrderStatus(reloaded.status).value,
            driver_user_id=driver.user_id if driver is not None else None,
        )
        return reloaded

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
        current_stop = get_current_stop(stops, OrderStatus(order.status))
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

    def finish_delivery(
        self,
        current_user: User,
        order_id: uuid.UUID,
        ip_address: str | None = None,
    ) -> Order:
        """Finish delivery after signed CMR upload (unloading complete at customer)."""
        order = self._get_workflow_order(current_user, order_id)
        order_status = OrderStatus(order.status)
        if order_status != OrderStatus.ARRIVED_DELIVERY:
            raise ValidationError(
                code="INVALID_ORDER_STATUS",
                message="Finish delivery is only available after signed CMR upload.",
            )

        stops = get_active_stops(
            self._stops.list_for_order(order.id, current_user.company_id)
        )
        delivery_stop = get_delivery_stop(stops)
        validate_current_stop_type(delivery_stop, StopType.DELIVERY)
        if delivery_stop is None:
            raise ValidationError(
                code="DELIVERY_STOP_NOT_FOUND",
                message="No active delivery stop found for this order.",
            )

        current_progress = StopProgressStatus(delivery_stop.progress_status)
        if current_progress != StopProgressStatus.DELIVERY_CONFIRMED:
            raise ValidationError(
                code="CMR_REQUIRED",
                message="Upload the signed CMR before finishing delivery.",
            )

        return self._transition(
            current_user,
            order,
            target_status=OrderStatus.DELIVERING,
            event_type="DELIVERY_FINISHED",
            description="Delivery finished.",
            ip_address=ip_address,
            notify_staff_type="DELIVERY_FINISHED",
            notify_staff_title="Delivery finished",
            notify_staff_message=(
                f"Driver finished delivery for order {order.order_number}."
            ),
        )

    def start_delivery(
        self,
        current_user: User,
        order_id: uuid.UUID,
        ip_address: str | None = None,
    ) -> Order:
        """Backward-compatible alias for finish_delivery."""
        return self.finish_delivery(current_user, order_id, ip_address)

    def confirm_delivery_cmr(
        self,
        current_user: User,
        order_id: uuid.UUID,
        ip_address: str | None = None,
    ) -> tuple[Order, OrderStop | None]:
        """Confirm delivery after signed CMR upload by advancing the delivery stop."""
        order = self._get_workflow_order(current_user, order_id)
        order_status = OrderStatus(order.status)
        if order_status != OrderStatus.ARRIVED_DELIVERY:
            raise ValidationError(
                code="INVALID_ORDER_STATUS",
                message="Signed CMR can only be uploaded after arriving at delivery.",
            )

        if not self._documents.has_signed_cmr_upload(order_id, current_user.company_id):
            raise ValidationError(
                code="CMR_REQUIRED",
                message="Upload the physically signed or stamped CMR copy.",
            )

        stops = get_active_stops(
            self._stops.list_for_order(order.id, current_user.company_id)
        )
        delivery_stop = get_delivery_stop(stops)
        validate_current_stop_type(delivery_stop, StopType.DELIVERY)
        if delivery_stop is None:
            raise ValidationError(
                code="DELIVERY_STOP_NOT_FOUND",
                message="No active delivery stop found for this order.",
            )

        current_progress = StopProgressStatus(delivery_stop.progress_status)
        updated_stop: OrderStop | None = delivery_stop
        logger.info(
            "Workflow confirm_delivery_cmr order_id=%s order_status=%s stop_progress=%s",
            order.id,
            order_status.value,
            current_progress.value,
        )

        if current_progress == StopProgressStatus.DELIVERY_CONFIRMED:
            reloaded = self._reload_order(current_user, order.id)
            return reloaded, updated_stop

        if current_progress != StopProgressStatus.ARRIVED:
            raise ValidationError(
                code="INVALID_STOP_PROGRESS",
                message=(
                    "Delivery stop must be arrived before CMR can be confirmed. "
                    f"Current progress is {current_progress.value}."
                ),
            )

        updated_stop = self._advance_stop_progress(
            delivery_stop,
            StopProgressStatus.DELIVERY_CONFIRMED,
            current_user.id,
        )
        self._timeline.record(
            current_user,
            order.id,
            "DELIVERY_CMR_CONFIRMED",
            "Signed CMR uploaded and delivery confirmed.",
        )
        reloaded = self._reload_order(current_user, order.id)
        driver = self._get_assigned_driver(reloaded)
        publish_order_event(
            company_id=current_user.company_id,
            order_id=reloaded.id,
            event_type=RealtimeEventType.ORDER_UPDATED,
            order_number=reloaded.order_number,
            status=OrderStatus(reloaded.status).value,
            driver_user_id=driver.user_id if driver is not None else None,
        )
        return reloaded, updated_stop

    def complete_delivery(
        self,
        current_user: User,
        order_id: uuid.UUID,
        ip_address: str | None = None,
    ) -> Order:
        """Complete the job after delivery is finished and signed CMR is attached."""
        order = self._get_workflow_order(current_user, order_id)
        order_status = OrderStatus(order.status)
        if order_status != OrderStatus.DELIVERING:
            raise ValidationError(
                code="INVALID_ORDER_STATUS",
                message="Finish delivery before completing the job.",
            )

        if not self._documents.has_signed_cmr_upload(order_id, current_user.company_id):
            raise ValidationError(
                code="CMR_REQUIRED",
                message="Upload the signed CMR before completing the job.",
            )

        stops = get_active_stops(
            self._stops.list_for_order(order.id, current_user.company_id)
        )
        delivery_stop = get_delivery_stop(stops)
        validate_current_stop_type(delivery_stop, StopType.DELIVERY)
        if delivery_stop is not None:
            current_progress = StopProgressStatus(delivery_stop.progress_status)
            logger.info(
                "Workflow complete_delivery order_id=%s order_status=%s stop_progress=%s",
                order.id,
                order.status,
                current_progress.value,
            )
            if current_progress != StopProgressStatus.DELIVERY_CONFIRMED:
                raise ValidationError(
                    code="CMR_REQUIRED",
                    message="Upload the signed CMR before completing the job.",
                )
            self._advance_stop_progress(
                delivery_stop,
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

    def _validate_loading_vehicles_ready(
        self,
        order_id: uuid.UUID,
        company_id: uuid.UUID,
    ) -> None:
        """Ensure every vehicle is registered and VIN-verified before loading completes."""
        vehicles = self._vehicles.list_for_order(order_id, company_id)
        if not vehicles:
            raise ValidationError(
                code="NO_VEHICLES",
                message="Add at least one vehicle before finishing loading.",
            )
        pending = [vehicle for vehicle in vehicles if not vehicle.verified_vin]
        if pending:
            raise ValidationError(
                code="VINS_NOT_VERIFIED",
                message=(
                    f"{len(pending)} vehicle(s) still need VIN verification "
                    "before loading can be completed."
                ),
            )

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
        current = StopProgressStatus(stop.progress_status)
        logger.info(
            "Workflow stop progress order_id=%s stop_id=%s %s -> %s",
            stop.order_id,
            stop.id,
            current.value,
            target_status.value,
        )
        validate_stop_progress_transition(stop, target_status)
        updated = self._stops.update_progress(stop, target_status, updated_by)
        logger.info(
            "Workflow stop progress committed order_id=%s stop_id=%s progress=%s",
            stop.order_id,
            updated.id,
            updated.progress_status,
        )
        return updated

    def _prepare_pickup_stop_for_loading(
        self,
        stop: OrderStop,
        updated_by: uuid.UUID,
    ) -> None:
        """Ensure pickup stop progress is ready before order enters LOADING."""
        current = StopProgressStatus(stop.progress_status)
        if current == StopProgressStatus.PENDING:
            logger.warning(
                "Pickup stop still pending at start_loading; auto-marking arrived order_id=%s stop_id=%s",
                stop.order_id,
                stop.id,
            )
            stop = self._advance_stop_progress(stop, StopProgressStatus.ARRIVED, updated_by)
        if StopProgressStatus(stop.progress_status) == StopProgressStatus.ARRIVED:
            self._advance_stop_progress(stop, StopProgressStatus.LOADING, updated_by)

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
        ensure_driver_forward_transition(current_user, previous_status, target_status)
        logger.info(
            "Workflow transition order_id=%s order_number=%s %s -> %s event=%s user_id=%s",
            order.id,
            order.order_number,
            previous_status.value,
            target_status.value,
            event_type,
            current_user.id,
        )
        updated_order = self._orders.update_status(order, target_status, current_user.id)
        logger.info(
            "Workflow transition committed order_id=%s persisted_status=%s",
            updated_order.id,
            updated_order.status,
        )
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
                order_id=order.id,
            )
        reloaded = self._reload_order(current_user, updated_order.id)
        driver = self._get_assigned_driver(reloaded)
        mapped = WORKFLOW_REALTIME_EVENTS.get(event_type, RealtimeEventType.ORDER_UPDATED)
        if event_type == "DELIVERY_COMPLETE" and OrderStatus(reloaded.status) != OrderStatus.COMPLETED:
            mapped = RealtimeEventType.ORDER_UPDATED
        publish_order_event(
            company_id=current_user.company_id,
            order_id=reloaded.id,
            event_type=mapped,
            order_number=reloaded.order_number,
            status=OrderStatus(reloaded.status).value,
            driver_user_id=driver.user_id if driver is not None else None,
        )
        return reloaded

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
