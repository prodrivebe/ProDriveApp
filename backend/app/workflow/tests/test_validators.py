"""Workflow validator unit tests."""

import pytest

from app.common.enums import OrderStatus, StopProgressStatus, StopType
from app.common.exceptions import ValidationError
from app.orders.models import OrderStop
from app.workflow.validators import (
    get_current_stop,
    validate_status_transition,
    validate_stop_progress_transition,
)


class _OrderStub:
    def __init__(self, status: OrderStatus) -> None:
        self.status = status


def test_validate_status_transition_accepts_full_chain() -> None:
    """Each workflow step accepts the previous status."""
    chain = [
        OrderStatus.ASSIGNED,
        OrderStatus.ACCEPTED,
        OrderStatus.ARRIVED_PICKUP,
        OrderStatus.LOADING,
        OrderStatus.LOADED,
        OrderStatus.IN_TRANSIT,
        OrderStatus.ARRIVED_DELIVERY,
        OrderStatus.DELIVERING,
        OrderStatus.COMPLETED,
    ]
    for current, target in zip(chain, chain[1:], strict=False):
        validate_status_transition(_OrderStub(current), target)


def test_validate_status_transition_rejects_skip() -> None:
    """Skipping workflow steps is rejected."""
    with pytest.raises(ValidationError) as exc:
        validate_status_transition(_OrderStub(OrderStatus.ASSIGNED), OrderStatus.LOADING)
    assert exc.value.code == "INVALID_ORDER_STATUS"


def test_get_current_stop_returns_first_incomplete() -> None:
    """Current stop is the first incomplete stop by sequence."""
    stops = [
        OrderStop(
            sequence=1,
            stop_type=StopType.PICKUP,
            progress_status=StopProgressStatus.COMPLETED,
        ),
        OrderStop(
            sequence=2,
            stop_type=StopType.DELIVERY,
            progress_status=StopProgressStatus.PENDING,
        ),
    ]
    current = get_current_stop(stops)
    assert current is not None
    assert current.sequence == 2


def test_validate_stop_progress_transition() -> None:
    """Stop progress follows pending → arrived → loading → completed."""
    stop = OrderStop(progress_status=StopProgressStatus.PENDING)
    validate_stop_progress_transition(stop, StopProgressStatus.ARRIVED)
