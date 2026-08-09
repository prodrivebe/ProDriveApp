"""Trailer capacity, height, and weight validation."""

from __future__ import annotations

import math
import uuid
from dataclasses import dataclass, field

from app.planning.loading_optimizer import (
    DEFAULT_LEGAL_HEIGHT_M,
    DEFAULT_VEHICLE_HEIGHT_M,
    DEFAULT_VEHICLE_WEIGHT_KG,
    PositionRecommendation,
    UPPER_DECK_CLEARANCE_M,
)


@dataclass
class ValidationIssue:
    """Single validation finding."""

    code: str
    message: str
    severity: str = "error"


@dataclass
class CapacityValidationResult:
    """Capacity validation output."""

    is_valid: bool
    errors: list[ValidationIssue] = field(default_factory=list)
    warnings: list[ValidationIssue] = field(default_factory=list)
    estimated_total_height_m: float = 0.0
    estimated_total_weight_kg: float = 0.0
    front_axle_percent: float = 50.0
    rear_axle_percent: float = 50.0

    def to_dict(self) -> dict[str, object]:
        return {
            "is_valid": self.is_valid,
            "errors": [issue.__dict__ for issue in self.errors],
            "warnings": [issue.__dict__ for issue in self.warnings],
            "estimated_total_height_m": self.estimated_total_height_m,
            "estimated_total_weight_kg": self.estimated_total_weight_kg,
            "front_axle_percent": self.front_axle_percent,
            "rear_axle_percent": self.rear_axle_percent,
        }


class CapacityValidator:
    """Validate loading plans against trailer and legal constraints."""

    def validate(
        self,
        *,
        trailer_capacity: int,
        trailer_max_height_m: float | None,
        trailer_max_weight_kg: float | None,
        trailer_type: str | None,
        positions: list[PositionRecommendation],
        vehicle_weights: dict[uuid.UUID, float],
        vehicle_heights: dict[uuid.UUID, float],
        unloading_sequence: list[uuid.UUID] | None = None,
    ) -> CapacityValidationResult:
        """Validate a proposed loading layout."""
        errors: list[ValidationIssue] = []
        warnings: list[ValidationIssue] = []

        if len(positions) > trailer_capacity:
            errors.append(
                ValidationIssue(
                    code="CAPACITY_EXCEEDED",
                    message=f"Position count {len(positions)} exceeds trailer capacity {trailer_capacity}.",
                )
            )

        slot_map: dict[int, uuid.UUID] = {}
        for position in positions:
            if position.trailer_position in slot_map:
                errors.append(
                    ValidationIssue(
                        code="DUPLICATE_POSITION",
                        message=f"Trailer position {position.trailer_position} is assigned twice.",
                    )
                )
            slot_map[position.trailer_position] = position.vehicle_id
            if position.trailer_position < 1 or position.trailer_position > trailer_capacity:
                errors.append(
                    ValidationIssue(
                        code="INVALID_POSITION",
                        message=f"Trailer position {position.trailer_position} is out of range.",
                    )
                )

        vehicle_ids = {position.vehicle_id for position in positions}
        if len(vehicle_ids) != len(positions):
            errors.append(
                ValidationIssue(
                    code="DUPLICATE_VEHICLE",
                    message="The same vehicle appears in multiple positions.",
                )
            )

        total_weight = 0.0
        max_height = 0.0
        for position in positions:
            weight = vehicle_weights.get(position.vehicle_id, DEFAULT_VEHICLE_WEIGHT_KG)
            height = vehicle_heights.get(position.vehicle_id, DEFAULT_VEHICLE_HEIGHT_M)
            total_weight += weight
            deck_height = height + (UPPER_DECK_CLEARANCE_M if position.upper_deck else 0.35)
            max_height = max(max_height, deck_height)
            if position.upper_deck and height > UPPER_DECK_CLEARANCE_M:
                warnings.append(
                    ValidationIssue(
                        code="UPPER_DECK_HEIGHT",
                        message=f"Vehicle at position {position.trailer_position} may not fit upper deck.",
                        severity="warning",
                    )
                )

        max_allowed_height = trailer_max_height_m or DEFAULT_LEGAL_HEIGHT_M
        max_allowed_weight = trailer_max_weight_kg or math.inf

        if total_weight > max_allowed_weight:
            errors.append(
                ValidationIssue(
                    code="WEIGHT_EXCEEDED",
                    message="Total weight exceeds trailer maximum.",
                )
            )
        if max_height > max_allowed_height:
            errors.append(
                ValidationIssue(
                    code="HEIGHT_EXCEEDED",
                    message="Estimated transport height exceeds trailer or legal limit.",
                )
            )

        if trailer_type and "incompatible" in trailer_type.lower():
            warnings.append(
                ValidationIssue(
                    code="TRAILER_COMPATIBILITY",
                    message="Trailer type may be incompatible with selected vehicles.",
                    severity="warning",
                )
            )

        front_weight = sum(
            vehicle_weights.get(position.vehicle_id, DEFAULT_VEHICLE_WEIGHT_KG)
            for position in positions
            if position.trailer_position <= math.ceil(max(len(positions), 1) / 2)
        )
        front_percent = round((front_weight / total_weight) * 100, 1) if total_weight else 50.0
        rear_percent = round(100 - front_percent, 1)

        if front_percent < 30 or front_percent > 70:
            warnings.append(
                ValidationIssue(
                    code="AXLE_BALANCE",
                    message="Axle distribution may be outside recommended range.",
                    severity="warning",
                )
            )

        if unloading_sequence:
            blocking = self._check_unloading_sequence(positions, unloading_sequence)
            if blocking:
                errors.append(
                    ValidationIssue(
                        code="IMPOSSIBLE_UNLOADING",
                        message=blocking,
                    )
                )

        return CapacityValidationResult(
            is_valid=not errors,
            errors=errors,
            warnings=warnings,
            estimated_total_height_m=round(max_height, 2),
            estimated_total_weight_kg=round(total_weight, 2),
            front_axle_percent=front_percent,
            rear_axle_percent=rear_percent,
        )

    @staticmethod
    def _check_unloading_sequence(
        positions: list[PositionRecommendation],
        unloading_sequence: list[uuid.UUID],
    ) -> str | None:
        """Detect vehicles blocked by others during unloading."""
        position_by_vehicle = {item.vehicle_id: item for item in positions}
        for index, vehicle_id in enumerate(unloading_sequence):
            current = position_by_vehicle.get(vehicle_id)
            if current is None:
                continue
            for later_id in unloading_sequence[index + 1 :]:
                later = position_by_vehicle.get(later_id)
                if later is None:
                    continue
                if later.trailer_position < current.trailer_position:
                    return (
                        "Unloading sequence requires removing a rear vehicle before "
                        "a forward vehicle — adjust positions or sequence."
                    )
        return None
