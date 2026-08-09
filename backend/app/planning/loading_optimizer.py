"""Loading recommendation engine — deterministic position optimization."""

from __future__ import annotations

import math
import uuid
from dataclasses import dataclass, field

DEFAULT_VEHICLE_WEIGHT_KG = 1500.0
DEFAULT_VEHICLE_HEIGHT_M = 1.55
DEFAULT_LEGAL_HEIGHT_M = 4.0
UPPER_DECK_CLEARANCE_M = 1.65


@dataclass
class VehicleLoadInput:
    """Vehicle inputs for loading optimization."""

    vehicle_id: uuid.UUID
    make: str | None
    model: str | None
    weight_kg: float
    height_m: float
    pickup_sequence: int
    delivery_sequence: int
    destination_city: str | None = None


@dataclass
class PositionRecommendation:
    """Recommended vehicle position on trailer."""

    vehicle_id: uuid.UUID
    vehicle_label: str
    upper_deck: bool
    trailer_position: int
    loading_order: int
    unloading_order: int
    destination_city: str | None = None
    weight_kg: float = 0.0
    height_m: float = 0.0


@dataclass
class LoadingOptimizationResult:
    """Full loading optimization output."""

    positions: list[PositionRecommendation] = field(default_factory=list)
    loading_sequence: list[uuid.UUID] = field(default_factory=list)
    unloading_sequence: list[uuid.UUID] = field(default_factory=list)
    estimated_total_height_m: float = 0.0
    estimated_total_weight_kg: float = 0.0
    front_axle_percent: float = 50.0
    rear_axle_percent: float = 50.0
    warnings: list[str] = field(default_factory=list)
    reasoning: list[str] = field(default_factory=list)
    confidence: float = 0.0

    def to_output_json(self) -> dict[str, object]:
        return {
            "positions": [
                {
                    "vehicle_id": str(item.vehicle_id),
                    "vehicle_label": item.vehicle_label,
                    "upper_deck": item.upper_deck,
                    "trailer_position": item.trailer_position,
                    "loading_order": item.loading_order,
                    "unloading_order": item.unloading_order,
                    "destination_city": item.destination_city,
                    "weight_kg": item.weight_kg,
                    "height_m": item.height_m,
                }
                for item in self.positions
            ],
            "loading_sequence": [str(item) for item in self.loading_sequence],
            "unloading_sequence": [str(item) for item in self.unloading_sequence],
            "estimated_total_height_m": self.estimated_total_height_m,
            "estimated_total_weight_kg": self.estimated_total_weight_kg,
            "front_axle_percent": self.front_axle_percent,
            "rear_axle_percent": self.rear_axle_percent,
            "warnings": self.warnings,
            "reasoning": self.reasoning,
            "confidence": self.confidence,
        }


class LoadingOptimizer:
    """Generate recommended trailer loading positions."""

    PROMPT_VERSION = "v1"
    MODEL_VERSION = "prodrive-heuristic-loading-1.0"

    def optimize(
        self,
        *,
        trailer_capacity: int,
        trailer_max_height_m: float | None,
        trailer_max_weight_kg: float | None,
        vehicles: list[VehicleLoadInput],
    ) -> LoadingOptimizationResult:
        """Build a loading plan from vehicle and trailer constraints."""
        if not vehicles:
            return LoadingOptimizationResult(confidence=0.1, warnings=["No vehicles to load."])

        max_height = trailer_max_height_m or DEFAULT_LEGAL_HEIGHT_M
        max_weight = trailer_max_weight_kg or math.inf
        bi_level = trailer_capacity >= 3
        lower_slots = max(1, math.ceil(trailer_capacity / 2)) if bi_level else trailer_capacity
        upper_slots = max(0, trailer_capacity - lower_slots)

        sorted_for_loading = sorted(
            vehicles,
            key=lambda item: (-item.delivery_sequence, item.height_m),
        )
        sorted_for_unloading = sorted(vehicles, key=lambda item: item.delivery_sequence)

        loading_rank = {
            vehicle.vehicle_id: index + 1 for index, vehicle in enumerate(sorted_for_loading)
        }
        unloading_rank = {
            vehicle.vehicle_id: index + 1 for index, vehicle in enumerate(sorted_for_unloading)
        }

        lower_candidates = sorted(
            vehicles,
            key=lambda item: (-item.height_m, item.delivery_sequence),
        )
        upper_candidates = sorted(
            vehicles,
            key=lambda item: (item.height_m, item.delivery_sequence),
        )

        positions: list[PositionRecommendation] = []
        reasoning: list[str] = [
            "Loading sequence follows reverse delivery order for accessible unloading.",
            "Shorter vehicles assigned to upper deck when bi-level trailer is used.",
        ]
        warnings: list[str] = []

        if bi_level:
            reasoning.append(f"Bi-level layout: {lower_slots} lower + {upper_slots} upper slots.")
        else:
            reasoning.append("Single-deck trailer layout applied.")

        lower_index = 0
        upper_index = 0
        assigned: set[uuid.UUID] = set()

        for slot in range(1, lower_slots + 1):
            if lower_index >= len(lower_candidates):
                break
            vehicle = lower_candidates[lower_index]
            while vehicle.vehicle_id in assigned and lower_index < len(lower_candidates) - 1:
                lower_index += 1
                vehicle = lower_candidates[lower_index]
            if vehicle.vehicle_id in assigned:
                continue
            assigned.add(vehicle.vehicle_id)
            positions.append(self._build_position(vehicle, False, slot, loading_rank, unloading_rank))
            lower_index += 1

        for slot in range(1, upper_slots + 1):
            trailer_position = lower_slots + slot
            if upper_index >= len(upper_candidates):
                break
            vehicle = upper_candidates[upper_index]
            while vehicle.vehicle_id in assigned and upper_index < len(upper_candidates) - 1:
                upper_index += 1
                vehicle = upper_candidates[upper_index]
            if vehicle.vehicle_id in assigned:
                continue
            if vehicle.height_m > UPPER_DECK_CLEARANCE_M:
                warnings.append(
                    f"Vehicle {vehicle.make or ''} {vehicle.model or ''} may exceed upper deck clearance."
                )
            assigned.add(vehicle.vehicle_id)
            positions.append(
                self._build_position(vehicle, True, trailer_position, loading_rank, unloading_rank)
            )
            upper_index += 1

        for vehicle in vehicles:
            if vehicle.vehicle_id not in assigned:
                warnings.append(f"Vehicle {vehicle.vehicle_id} could not be assigned a slot.")

        total_weight = sum(item.weight_kg for item in vehicles)
        max_vehicle_height = max(item.height_m for item in vehicles) if vehicles else 0.0
        estimated_height = max_vehicle_height + (UPPER_DECK_CLEARANCE_M if bi_level else 0.35)

        if total_weight > max_weight:
            warnings.append("Total vehicle weight exceeds trailer maximum weight.")
        if estimated_height > max_height:
            warnings.append("Estimated transport height may exceed legal or trailer limit.")
        if len(vehicles) > trailer_capacity:
            warnings.append("Vehicle count exceeds trailer capacity.")

        front_weight = sum(
            item.weight_kg for item in positions if item.trailer_position <= math.ceil(len(positions) / 2)
        )
        front_percent = round((front_weight / total_weight) * 100, 1) if total_weight else 50.0
        rear_percent = round(100 - front_percent, 1)

        if front_percent < 30 or front_percent > 70:
            warnings.append("Axle balance may be outside recommended 40/60 range.")

        confidence = 0.85
        if warnings:
            confidence -= min(0.35, 0.08 * len(warnings))
        confidence = round(max(0.35, confidence), 2)

        return LoadingOptimizationResult(
            positions=sorted(positions, key=lambda item: item.trailer_position),
            loading_sequence=[item.vehicle_id for item in sorted_for_loading],
            unloading_sequence=[item.vehicle_id for item in sorted_for_unloading],
            estimated_total_height_m=round(estimated_height, 2),
            estimated_total_weight_kg=round(total_weight, 2),
            front_axle_percent=front_percent,
            rear_axle_percent=rear_percent,
            warnings=warnings,
            reasoning=reasoning,
            confidence=confidence,
        )

    @staticmethod
    def _build_position(
        vehicle: VehicleLoadInput,
        upper_deck: bool,
        trailer_position: int,
        loading_rank: dict[uuid.UUID, int],
        unloading_rank: dict[uuid.UUID, int],
    ) -> PositionRecommendation:
        label = " ".join(part for part in [vehicle.make, vehicle.model] if part).strip() or str(
            vehicle.vehicle_id
        )[:8]
        return PositionRecommendation(
            vehicle_id=vehicle.vehicle_id,
            vehicle_label=label,
            upper_deck=upper_deck,
            trailer_position=trailer_position,
            loading_order=loading_rank[vehicle.vehicle_id],
            unloading_order=unloading_rank[vehicle.vehicle_id],
            destination_city=vehicle.destination_city,
            weight_kg=vehicle.weight_kg,
            height_m=vehicle.height_m,
        )
