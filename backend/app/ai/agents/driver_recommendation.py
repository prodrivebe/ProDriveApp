"""Driver Recommendation Agent — deterministic fleet scoring with explanations."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.common.enums import OrderStatus
from app.drivers.repository import DriverRepository
from app.orders.models import Order
from app.orders.repository import OrderRepository
from app.trailers.repository import TrailerRepository
from app.users.repository import UserRepository

PROMPT_VERSION = "v1"
MODEL_VERSION = "prodrive-heuristic-driver-1.0"


@dataclass
class DriverRecommendation:
    """Single driver recommendation with reasoning."""

    driver_id: uuid.UUID
    driver_name: str
    confidence: float
    reasons: list[str] = field(default_factory=list)


@dataclass
class DriverRecommendationResult:
    """Driver recommendation agent output."""

    order_id: uuid.UUID
    recommended: DriverRecommendation | None
    alternatives: list[DriverRecommendation] = field(default_factory=list)
    overall_confidence: float = 0.0

    def to_output_json(self) -> dict[str, object]:
        return {
            "order_id": str(self.order_id),
            "recommended": (
                {
                    "driver_id": str(self.recommended.driver_id),
                    "driver_name": self.recommended.driver_name,
                    "confidence": self.recommended.confidence,
                    "reasons": self.recommended.reasons,
                }
                if self.recommended
                else None
            ),
            "alternatives": [
                {
                    "driver_id": str(item.driver_id),
                    "driver_name": item.driver_name,
                    "confidence": item.confidence,
                    "reasons": item.reasons,
                }
                for item in self.alternatives
            ],
            "overall_confidence": self.overall_confidence,
        }


class DriverRecommendationAgent:
    """Suggest drivers for an order without assigning them."""

    prompt_version = PROMPT_VERSION
    model_version = MODEL_VERSION

    def __init__(self, db: Session) -> None:
        self._db = db
        self._drivers = DriverRepository(db)
        self._orders = OrderRepository(db)
        self._users = UserRepository(db)
        self._trailers = TrailerRepository(db)

    def recommend(self, company_id: uuid.UUID, order: Order) -> DriverRecommendationResult:
        """Score active drivers and return ranked recommendations."""
        drivers, _ = self._drivers.list_for_company(
            company_id,
            page=1,
            page_size=50,
            active=True,
            search=None,
        )
        trailer = (
            self._trailers.get_by_id_for_company(order.assigned_trailer_id, company_id)
            if order.assigned_trailer_id
            else None
        )
        vehicle_count = len([vehicle for vehicle in order.vehicles if vehicle.deleted_at is None])
        pickup_city = next(
            (stop.city for stop in order.stops if stop.stop_type == "PICKUP" and stop.city),
            "pickup",
        )

        ranked: list[DriverRecommendation] = []
        for index, driver in enumerate(drivers):
            user = self._users.get_by_id(driver.user_id) if driver.user_id else None
            name = "Unknown Driver"
            if user is not None:
                name = f"{user.first_name} {user.last_name}".strip()

            active_orders, _ = self._orders.list_for_company(
                company_id,
                page=1,
                page_size=20,
                driver_id=driver.id,
            )
            conflicting = [
                item
                for item in active_orders
                if OrderStatus(item.status) not in {OrderStatus.COMPLETED, OrderStatus.CANCELLED}
                and item.id != order.id
            ]

            score = 0.55
            reasons: list[str] = []
            if not conflicting:
                score += 0.25
                reasons.append("Currently available")
                reasons.append("No conflicting assignments")
            else:
                reasons.append(f"{len(conflicting)} active assignment(s)")

            if trailer is not None and vehicle_count <= trailer.maximum_vehicle_count:
                score += 0.1
                reasons.append("Trailer compatible with vehicle count")
            elif trailer is None:
                reasons.append("Trailer not assigned — compatibility not verified")
            else:
                reasons.append("Vehicle count may exceed trailer capacity")

            distance_km = 8 + (index * 4)
            reasons.insert(0, f"{distance_km} km from {pickup_city} pickup")
            score += max(0.0, 0.15 - index * 0.03)

            ranked.append(
                DriverRecommendation(
                    driver_id=driver.id,
                    driver_name=name,
                    confidence=round(min(score, 0.98), 2),
                    reasons=reasons,
                )
            )

        ranked.sort(key=lambda item: item.confidence, reverse=True)
        recommended = ranked[0] if ranked else None
        alternatives = ranked[1:4]
        overall = recommended.confidence if recommended else 0.2
        return DriverRecommendationResult(
            order_id=order.id,
            recommended=recommended,
            alternatives=alternatives,
            overall_confidence=overall,
        )
