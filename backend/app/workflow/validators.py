"""Driver operational workflow validation."""

from app.common.enums import OrderStatus, StopProgressStatus, StopType, UserRole
from app.common.exceptions import ValidationError
from app.orders.models import Order, OrderStop
from app.users.models import User

TERMINAL_STATUSES = {OrderStatus.COMPLETED, OrderStatus.CANCELLED}

WORKFLOW_TRANSITIONS: dict[OrderStatus, set[OrderStatus]] = {
    OrderStatus.READY: {OrderStatus.DRAFT, OrderStatus.ASSIGNED},
    OrderStatus.ASSIGNED: {OrderStatus.DRAFT, OrderStatus.READY},
    OrderStatus.ACCEPTED: {OrderStatus.ASSIGNED, OrderStatus.LOADING},
    OrderStatus.ARRIVED_PICKUP: {OrderStatus.ACCEPTED},
    OrderStatus.LOADING: {OrderStatus.ARRIVED_PICKUP},
    OrderStatus.LOADED: {OrderStatus.LOADING},
    OrderStatus.IN_TRANSIT: {OrderStatus.LOADED},
    OrderStatus.ARRIVED_DELIVERY: {OrderStatus.IN_TRANSIT},
    OrderStatus.DELIVERING: {OrderStatus.ARRIVED_DELIVERY},
    OrderStatus.COMPLETED: {OrderStatus.DELIVERING},
}

STOP_PROGRESS_TRANSITIONS: dict[StopProgressStatus, set[StopProgressStatus]] = {
    StopProgressStatus.ARRIVED: {StopProgressStatus.PENDING},
    StopProgressStatus.LOADING: {StopProgressStatus.ARRIVED},
    StopProgressStatus.DELIVERY_CONFIRMED: {
        StopProgressStatus.ARRIVED,
        StopProgressStatus.LOADING,
    },
    StopProgressStatus.COMPLETED: {
        StopProgressStatus.LOADING,
        StopProgressStatus.DELIVERY_CONFIRMED,
    },
}

NEXT_REQUIRED_ACTIONS: dict[OrderStatus, str] = {
    OrderStatus.ASSIGNED: "Accept or reject this order",
    OrderStatus.ACCEPTED: "Navigate to pickup and confirm arrival",
    OrderStatus.ARRIVED_PICKUP: "Start loading vehicles",
    OrderStatus.LOADING: "Generate CMR and complete loading",
    OrderStatus.LOADED: "Start transit to the next stop",
    OrderStatus.IN_TRANSIT: "Navigate to delivery and confirm arrival",
    OrderStatus.ARRIVED_DELIVERY: "Upload signed CMR and finish delivery",
    OrderStatus.DELIVERING: "Complete the job",
    OrderStatus.COMPLETED: "No active tasks",
    OrderStatus.CANCELLED: "No active tasks",
    OrderStatus.READY: "Waiting for assignment",
    OrderStatus.DRAFT: "Waiting for assignment",
}

ACTIVE_WORKFLOW_STATUSES = {
    OrderStatus.ASSIGNED,
    OrderStatus.ACCEPTED,
    OrderStatus.ARRIVED_PICKUP,
    OrderStatus.LOADING,
    OrderStatus.LOADED,
    OrderStatus.IN_TRANSIT,
    OrderStatus.ARRIVED_DELIVERY,
    OrderStatus.DELIVERING,
}

PICKUP_PHASE_STATUSES = {
    OrderStatus.ACCEPTED,
    OrderStatus.ARRIVED_PICKUP,
    OrderStatus.LOADING,
    OrderStatus.LOADED,
}

DELIVERY_PHASE_STATUSES = {
    OrderStatus.IN_TRANSIT,
    OrderStatus.ARRIVED_DELIVERY,
    OrderStatus.DELIVERING,
}

DRIVER_FORWARD_STATUSES: tuple[OrderStatus, ...] = (
    OrderStatus.ASSIGNED,
    OrderStatus.ACCEPTED,
    OrderStatus.ARRIVED_PICKUP,
    OrderStatus.LOADING,
    OrderStatus.LOADED,
    OrderStatus.IN_TRANSIT,
    OrderStatus.ARRIVED_DELIVERY,
    OrderStatus.DELIVERING,
    OrderStatus.COMPLETED,
)


def _stop_sort_key(stop: OrderStop) -> tuple[int, int]:
    """Sort by sequence, then pickup before delivery for duplicate sequences."""
    type_rank = 0 if stop.stop_type == StopType.PICKUP else 1
    return (stop.sequence, type_rank)


def validate_order_in_workflow(order: Order) -> None:
    """Ensure an order can continue through the driver workflow."""
    if OrderStatus(order.status) in TERMINAL_STATUSES:
        raise ValidationError(
            code="ORDER_NOT_EDITABLE",
            message="Completed or cancelled orders cannot continue.",
        )


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


def ensure_driver_forward_transition(
    current_user: User,
    current_status: OrderStatus,
    target_status: OrderStatus,
) -> None:
    """Drivers may only advance workflow forward; dispatchers use dedicated reopen actions."""
    if current_user.role != UserRole.DRIVER:
        return
    if target_status == OrderStatus.CANCELLED:
        return
    if (
        current_status == OrderStatus.LOADING
        and target_status == OrderStatus.ACCEPTED
    ):
        return

    try:
        current_index = DRIVER_FORWARD_STATUSES.index(current_status)
        target_index = DRIVER_FORWARD_STATUSES.index(target_status)
    except ValueError:
        raise ValidationError(
            code="INVALID_ORDER_STATUS",
            message=f"Cannot transition order from {current_status} to {target_status}.",
        ) from None

    if target_index <= current_index:
        raise ValidationError(
            code="INVALID_ORDER_STATUS",
            message="Drivers cannot move the workflow backward. Contact your dispatcher.",
        )


def validate_stop_progress_transition(
    stop: OrderStop,
    target_status: StopProgressStatus,
) -> None:
    """Ensure a stop progress transition is allowed."""
    current_status = StopProgressStatus(stop.progress_status)
    allowed_sources = STOP_PROGRESS_TRANSITIONS.get(target_status, set())
    if current_status not in allowed_sources:
        raise ValidationError(
            code="INVALID_STOP_PROGRESS",
            message=(
                f"Cannot transition stop from {current_status} to {target_status}."
            ),
        )


def get_active_stops(stops: list[OrderStop]) -> list[OrderStop]:
    """Return non-deleted stops sorted by sequence and stop type."""
    active = [stop for stop in stops if stop.deleted_at is None]
    active.sort(key=_stop_sort_key)
    return active


def get_pickup_stop(
    stops: list[OrderStop],
    *,
    require_incomplete: bool = True,
) -> OrderStop | None:
    """Return the active pickup stop for loading workflow actions."""
    pickup_stops = [
        stop
        for stop in get_active_stops(stops)
        if stop.stop_type == StopType.PICKUP
        and (
            not require_incomplete
            or StopProgressStatus(stop.progress_status) != StopProgressStatus.COMPLETED
        )
    ]
    return pickup_stops[0] if pickup_stops else None


def get_delivery_stop(
    stops: list[OrderStop],
    *,
    require_incomplete: bool = True,
) -> OrderStop | None:
    """Return the active delivery stop for delivery workflow actions."""
    delivery_stops = [
        stop
        for stop in get_active_stops(stops)
        if stop.stop_type == StopType.DELIVERY
        and (
            not require_incomplete
            or StopProgressStatus(stop.progress_status) != StopProgressStatus.COMPLETED
        )
    ]
    return delivery_stops[0] if delivery_stops else None


def get_current_stop(
    stops: list[OrderStop],
    order_status: OrderStatus | None = None,
) -> OrderStop | None:
    """Return the next stop the driver must complete."""
    incomplete = [
        stop
        for stop in get_active_stops(stops)
        if StopProgressStatus(stop.progress_status) != StopProgressStatus.COMPLETED
    ]
    if not incomplete:
        return None

    if order_status in PICKUP_PHASE_STATUSES:
        for stop in incomplete:
            if stop.stop_type == StopType.PICKUP:
                return stop
    if order_status in DELIVERY_PHASE_STATUSES:
        for stop in incomplete:
            if stop.stop_type == StopType.DELIVERY:
                return stop

    return incomplete[0]


def get_remaining_stops(
    stops: list[OrderStop],
    current_stop: OrderStop | None,
) -> list[OrderStop]:
    """Return future stops after the current stop."""
    active = get_active_stops(stops)
    if current_stop is None:
        return active
    remaining: list[OrderStop] = []
    seen_current = False
    for stop in active:
        if stop.id == current_stop.id:
            seen_current = True
            continue
        if seen_current:
            remaining.append(stop)
    return remaining


def all_pickups_completed(stops: list[OrderStop]) -> bool:
    """Return whether every pickup stop is completed."""
    pickup_stops = [
        stop for stop in get_active_stops(stops) if stop.stop_type == StopType.PICKUP
    ]
    if not pickup_stops:
        return True
    return all(
        StopProgressStatus(stop.progress_status) == StopProgressStatus.COMPLETED
        for stop in pickup_stops
    )


def all_deliveries_completed(stops: list[OrderStop]) -> bool:
    """Return whether every delivery stop is completed."""
    delivery_stops = [
        stop for stop in get_active_stops(stops) if stop.stop_type == StopType.DELIVERY
    ]
    if not delivery_stops:
        return True
    return all(
        StopProgressStatus(stop.progress_status) == StopProgressStatus.COMPLETED
        for stop in delivery_stops
    )


def validate_current_stop_type(stop: OrderStop | None, expected: StopType) -> None:
    """Ensure the current stop matches the expected stop type."""
    if stop is None:
        return
    if stop.stop_type != expected:
        raise ValidationError(
            code="INVALID_STOP_TYPE",
            message=f"Current stop must be a {expected.value.lower()} stop.",
        )
