"""Order validation helpers."""

import re
import uuid

from app.common.enums import OrderStatus, StopType, UserRole
from app.common.exceptions import AuthorizationError, ValidationError
from app.drivers.models import Driver
from app.orders.models import Order, OrderStop
from app.orders.schemas import OrderStopCreateRequest, OrderVehicleCreateRequest
from app.users.models import User

VIN_PATTERN = re.compile(r"^[A-HJ-NPR-Z0-9]{17}$")

TERMINAL_STATUSES = {OrderStatus.COMPLETED, OrderStatus.CANCELLED}


def normalize_vin(vin: str) -> str:
    """Normalize and validate a vehicle VIN."""
    normalized = vin.strip().upper()
    if not VIN_PATTERN.match(normalized):
        raise ValidationError(
            code="INVALID_VIN",
            message="VIN must be 17 characters and exclude I, O, and Q.",
        )
    return normalized


def validate_order_editable(order: Order) -> None:
    """Ensure an order can still be edited."""
    if order.status in TERMINAL_STATUSES:
        raise ValidationError(
            code="ORDER_NOT_EDITABLE",
            message="Completed or cancelled orders cannot be modified.",
        )


WORKFLOW_TRANSITIONS: dict[OrderStatus, set[OrderStatus]] = {
    OrderStatus.READY: {OrderStatus.DRAFT, OrderStatus.ASSIGNED},
    OrderStatus.ASSIGNED: {OrderStatus.DRAFT, OrderStatus.READY},
    OrderStatus.ACCEPTED: {OrderStatus.ASSIGNED},
    OrderStatus.LOADING: {OrderStatus.ACCEPTED},
    OrderStatus.IN_TRANSIT: {OrderStatus.LOADING},
    OrderStatus.DELIVERING: {OrderStatus.IN_TRANSIT},
    OrderStatus.COMPLETED: {OrderStatus.DELIVERING},
}


def validate_status_transition(order: Order, target_status: OrderStatus) -> None:
    """Ensure a workflow transition is allowed."""
    current_status = OrderStatus(order.status)
    if target_status == OrderStatus.CANCELLED:
        if current_status in TERMINAL_STATUSES:
            raise ValidationError(
                code="INVALID_ORDER_STATUS",
                message="This order can no longer be cancelled.",
            )
        return

    allowed_sources = WORKFLOW_TRANSITIONS.get(target_status, set())
    if current_status not in allowed_sources:
        raise ValidationError(
            code="INVALID_ORDER_STATUS",
            message=f"Cannot transition order from {current_status} to {target_status}.",
        )


def validate_stop_sequences(stops: list[OrderStopCreateRequest]) -> None:
    """Ensure stop sequences are unique within the payload."""
    sequences = [stop.sequence for stop in stops]
    if len(sequences) != len(set(sequences)):
        raise ValidationError(
            code="DUPLICATE_STOP_SEQUENCE",
            message="Stop sequence values must be unique.",
        )


def validate_vehicle_stop_links(
    stops: list[OrderStop],
    payload: OrderVehicleCreateRequest,
) -> None:
    """Ensure vehicle stop references belong to the order and match stop types."""
    stop_map = {stop.id: stop for stop in stops}
    if payload.pickup_stop_id is not None:
        pickup_stop = stop_map.get(payload.pickup_stop_id)
        if pickup_stop is None or pickup_stop.stop_type != StopType.PICKUP:
            raise ValidationError(
                code="INVALID_PICKUP_STOP",
                message="Pickup stop must belong to the order and be a pickup stop.",
            )
    if payload.delivery_stop_id is not None:
        delivery_stop = stop_map.get(payload.delivery_stop_id)
        if delivery_stop is None or delivery_stop.stop_type != StopType.DELIVERY:
            raise ValidationError(
                code="INVALID_DELIVERY_STOP",
                message="Delivery stop must belong to the order and be a delivery stop.",
            )


def ensure_workflow_actor(
    current_user: User,
    order: Order,
    driver: Driver | None,
) -> None:
    """Ensure the user can perform a driver workflow action."""
    if current_user.role in {UserRole.ADMIN, UserRole.DISPATCHER}:
        return
    if driver is None or driver.user_id != current_user.id:
        raise AuthorizationError(
            code="FORBIDDEN",
            message="Only the assigned driver can perform this action.",
        )


def ensure_order_view_access(
    current_user: User,
    order: Order,
    driver: Driver | None,
) -> None:
    """Ensure the user can view an order."""
    if current_user.role in {UserRole.ADMIN, UserRole.DISPATCHER}:
        return
    if driver is None or driver.user_id != current_user.id:
        raise AuthorizationError(
            code="FORBIDDEN",
            message="You do not have permission to view this order.",
        )
