"""Trailer validation helpers."""

from app.common.enums import TrailerCapacity
from app.common.exceptions import ValidationError


def validate_trailer_capacity(maximum_vehicle_count: int) -> None:
    """Ensure trailer capacity is supported in Version 1."""
    if maximum_vehicle_count not in TrailerCapacity.values():
        raise ValidationError(
            code="INVALID_TRAILER_CAPACITY",
            message="Trailer capacity must be one of: 2, 3, 5, 8, 10.",
        )
