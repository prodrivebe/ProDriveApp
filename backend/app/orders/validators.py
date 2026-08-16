"""Order validation helpers."""

import re
from typing import TYPE_CHECKING

from app.common.enums import OrderStatus, StopType, UserRole
from app.common.exceptions import AuthorizationError, ValidationError
from app.drivers.models import Driver
from app.order_stops.validators import validate_stop_sequences
from app.orders.models import Order, OrderStop
from app.users.models import User

if TYPE_CHECKING:
    from app.orders.schemas import OrderVehicleCreateRequest

VIN_PATTERN = re.compile(r"^[A-HJ-NPR-Z0-9]{17}$")
MAX_ORDER_VEHICLES = 8

TERMINAL_STATUSES = {OrderStatus.COMPLETED, OrderStatus.CANCELLED}

LOADING_LOCKED_STATUSES = {
    OrderStatus.LOADED,
    OrderStatus.IN_TRANSIT,
    OrderStatus.ARRIVED_DELIVERY,
    OrderStatus.DELIVERING,
}


def validate_vehicle_count(count: int) -> None:
    """Ensure an order does not exceed the maximum vehicle limit."""
    if count > MAX_ORDER_VEHICLES:
        raise ValidationError(
            code="TOO_MANY_VEHICLES",
            message=f"An order may contain at most {MAX_ORDER_VEHICLES} vehicles.",
        )


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


def is_loading_locked(status: OrderStatus | str) -> bool:
    """Return whether vehicle editing is locked after loading completed."""
    resolved = OrderStatus(status) if isinstance(status, str) else status
    return resolved in LOADING_LOCKED_STATUSES


def ensure_vehicles_editable(order: Order) -> None:
    """Ensure vehicles on an order can still be added or modified."""
    validate_order_editable(order)
    if is_loading_locked(order.status):
        raise ValidationError(
            code="LOADING_LOCKED",
            message=(
                "Vehicle editing is locked after loading completed. "
                "Contact dispatcher to reopen loading."
            ),
        )


def validate_status_transition(order: Order, target_status: OrderStatus) -> None:
    """Ensure a workflow transition is allowed."""
    from app.workflow.validators import validate_status_transition as validate_workflow_status

    validate_workflow_status(order, target_status)


def validate_vehicle_stop_links(
    stops: list[OrderStop],
    payload: "OrderVehicleCreateRequest",
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
