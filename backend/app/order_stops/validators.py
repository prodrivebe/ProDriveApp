"""Order stop validation helpers."""

import uuid

from app.common.exceptions import ValidationError
from app.orders.models import OrderStop
from app.order_stops.schemas import OrderStopCreateRequest


def validate_stop_sequences(stops: list[OrderStopCreateRequest]) -> None:
    """Ensure stop sequences are unique within the payload."""
    sequences = [stop.sequence for stop in stops]
    if len(sequences) != len(set(sequences)):
        raise ValidationError(
            code="DUPLICATE_STOP_SEQUENCE",
            message="Stop sequence values must be unique.",
        )


def validate_stop_sequence_for_order(
    existing_stops: list[OrderStop],
    sequence: int,
    *,
    exclude_stop_id: uuid.UUID | None = None,
) -> None:
    """Ensure a stop sequence is unique within an order."""
    for stop in existing_stops:
        if exclude_stop_id is not None and stop.id == exclude_stop_id:
            continue
        if stop.sequence == sequence:
            raise ValidationError(
                code="DUPLICATE_STOP_SEQUENCE",
                message="Stop sequence values must be unique within the order.",
            )
