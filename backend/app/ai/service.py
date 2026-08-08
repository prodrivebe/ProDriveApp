"""AI business logic."""

import re

from sqlalchemy.orm import Session

from app.ai.schemas import (
    DriverSuggestion,
    EmptyKmSuggestion,
    LoadingPositionSuggestion,
    OrderQualityResponse,
    OrderScopedRequest,
    ParsedOrderDraft,
    ParseOrderRequest,
    RouteStopSuggestion,
    SuggestDriverResponse,
    SuggestEmptyKmResponse,
    SuggestLoadingResponse,
    SuggestRouteResponse,
)
from app.common.enums import OrderStatus, StopType
from app.drivers.repository import DriverRepository
from app.orders.repository import OrderRepository
from app.orders.schemas import OrderStopCreateRequest, OrderVehicleCreateRequest
from app.orders.service import OrderService
from app.users.models import User
from app.users.repository import UserRepository

VEHICLE_LINE_PATTERN = re.compile(
    r"^\s*(?:\d+[\).:-]\s*)?([A-Za-z]+(?:\s+[A-Za-z0-9.-]+)+)\s*$"
)
SECTION_PATTERN = re.compile(
    r"(?is)(pick\s*up|pickup|collection)\s*:?\s*(.*?)(deliver|delivery|drop\s*off|$)"
)


class AIService:
    """Version 1 AI helpers that never mutate business data."""

    def __init__(self, db: Session) -> None:
        self._db = db
        self._orders = OrderService(db)
        self._order_repo = OrderRepository(db)
        self._drivers = DriverRepository(db)
        self._users = UserRepository(db)

    def parse_order(self, payload: ParseOrderRequest) -> ParsedOrderDraft:
        """Extract a draft order structure from unstructured text."""
        message = payload.message.strip()
        pickup_stops: list[OrderStopCreateRequest] = []
        delivery_stops: list[OrderStopCreateRequest] = []
        vehicles: list[OrderVehicleCreateRequest] = []

        section_match = SECTION_PATTERN.search(message)
        if section_match:
            pickup_text = section_match.group(2)
            delivery_text = message[section_match.end(2) :]
            pickup_lines = [line.strip() for line in pickup_text.splitlines() if line.strip()]
            delivery_lines = [line.strip() for line in delivery_text.splitlines() if line.strip()]

            pickup_sequence = 1
            for line in pickup_lines:
                vehicle_match = VEHICLE_LINE_PATTERN.match(line)
                if vehicle_match and not self._looks_like_location(line):
                    make_model = vehicle_match.group(1).split(maxsplit=1)
                    vehicles.append(
                        OrderVehicleCreateRequest(
                            make=make_model[0],
                            model=make_model[1] if len(make_model) > 1 else None,
                        )
                    )
                elif self._looks_like_location(line):
                    pickup_stops.append(
                        OrderStopCreateRequest(
                            stop_type=StopType.PICKUP,
                            sequence=pickup_sequence,
                            city=line,
                        )
                    )
                    pickup_sequence += 1

            delivery_sequence = 1
            for line in delivery_lines:
                if self._looks_like_location(line):
                    delivery_stops.append(
                        OrderStopCreateRequest(
                            stop_type=StopType.DELIVERY,
                            sequence=delivery_sequence,
                            city=line,
                        )
                    )
                    delivery_sequence += 1

        missing_fields: list[str] = []
        if not pickup_stops:
            missing_fields.append("pickup_stops")
        if not delivery_stops:
            missing_fields.append("delivery_stops")
        if not vehicles:
            missing_fields.append("vehicles")

        extracted_count = len(pickup_stops) + len(delivery_stops) + len(vehicles)
        confidence_score = min(1.0, extracted_count / 4) if extracted_count else 0.1

        return ParsedOrderDraft(
            pickup_stops=pickup_stops,
            delivery_stops=[*delivery_stops],
            vehicles=vehicles,
            planned_pickup_date=None,
            planned_delivery_date=None,
            missing_fields=missing_fields,
            confidence_score=confidence_score,
        )

    def suggest_driver(
        self,
        current_user: User,
        payload: OrderScopedRequest,
    ) -> SuggestDriverResponse:
        """Suggest drivers for an order using simple active-driver heuristics."""
        self._orders.get_order(current_user, payload.order_id)
        drivers, _ = self._drivers.list_for_company(
            current_user.company_id,
            page=1,
            page_size=25,
            active=True,
            search=None,
        )
        suggestions: list[DriverSuggestion] = []
        for index, driver in enumerate(drivers):
            user = self._users.get_by_id(driver.user_id)
            name = "Unknown Driver"
            if user is not None:
                name = f"{user.first_name} {user.last_name}".strip()
            suggestions.append(
                DriverSuggestion(
                    driver_id=driver.id,
                    driver_name=name,
                    score=max(0.4, 0.9 - index * 0.1),
                    reason="Active driver available in company fleet.",
                )
            )
        recommended = suggestions[0] if suggestions else None
        alternatives = suggestions[1:4]
        return SuggestDriverResponse(recommended=recommended, alternatives=alternatives)

    def suggest_route(
        self,
        current_user: User,
        payload: OrderScopedRequest,
    ) -> SuggestRouteResponse:
        """Suggest stop order based on current pickup/delivery sequence."""
        order = self._orders.get_order(current_user, payload.order_id)
        stops = [
            RouteStopSuggestion(
                stop_id=stop.id,
                sequence=stop.sequence,
                stop_type=StopType(stop.stop_type),
            )
            for stop in sorted(order.stops, key=lambda item: item.sequence)
        ]
        confidence = 0.8 if stops else 0.2
        return SuggestRouteResponse(stops=stops, confidence_score=confidence)

    def suggest_loading(
        self,
        current_user: User,
        payload: OrderScopedRequest,
    ) -> SuggestLoadingResponse:
        """Suggest basic loading positions for vehicles on an order."""
        order = self._orders.get_order(current_user, payload.order_id)
        positions = [
            LoadingPositionSuggestion(
                vehicle_id=vehicle.id,
                loading_order=index + 1,
                trailer_position=index + 1,
            )
            for index, vehicle in enumerate(order.vehicles)
        ]
        confidence = 0.7 if positions else 0.2
        return SuggestLoadingResponse(positions=positions, confidence_score=confidence)

    def score_order_quality(
        self,
        current_user: User,
        payload: OrderScopedRequest,
    ) -> OrderQualityResponse:
        """Score order completeness for dispatcher review."""
        order = self._orders.get_order(current_user, payload.order_id)
        missing_fields: list[str] = []
        warnings: list[str] = []
        score = 1.0

        if not order.stops:
            missing_fields.append("stops")
            score -= 0.25
        if not order.vehicles:
            missing_fields.append("vehicles")
            score -= 0.25
        if order.assigned_driver_id is None:
            missing_fields.append("assigned_driver")
            score -= 0.15
        if order.planned_pickup_date is None:
            warnings.append("planned_pickup_date is missing")
            score -= 0.1
        if order.planned_delivery_date is None:
            warnings.append("planned_delivery_date is missing")
            score -= 0.1
        for vehicle in order.vehicles:
            if not vehicle.vin:
                warnings.append(f"Vehicle {vehicle.id} is missing VIN")

        return OrderQualityResponse(
            score=max(0.0, round(score, 2)),
            missing_fields=missing_fields,
            warnings=warnings,
        )

    def suggest_empty_km(self, current_user: User) -> SuggestEmptyKmResponse:
        """Suggest empty-km reduction opportunities using simple heuristics."""
        drivers, _ = self._drivers.list_for_company(
            current_user.company_id,
            page=1,
            page_size=50,
            active=True,
            search=None,
        )
        suggestions: list[EmptyKmSuggestion] = []
        for driver in drivers:
            orders, _ = self._order_repo.list_for_company(
                current_user.company_id,
                page=1,
                page_size=10,
                driver_id=driver.id,
            )
            active = [
                order
                for order in orders
                if OrderStatus(order.status)
                not in {OrderStatus.COMPLETED, OrderStatus.CANCELLED}
            ]
            if active:
                continue
            user = self._users.get_by_id(driver.user_id)
            name = "Unknown Driver"
            if user is not None:
                name = f"{user.first_name} {user.last_name}".strip()
            suggestions.append(
                EmptyKmSuggestion(
                    driver_id=driver.id,
                    driver_name=name,
                    suggested_route="Return to depot or pick up next READY order",
                    estimated_empty_km=45.0,
                    reason="Driver has no active assignments.",
                )
            )
        confidence = 0.6 if suggestions else 0.2
        return SuggestEmptyKmResponse(suggestions=suggestions[:5], confidence_score=confidence)

    @staticmethod
    def _looks_like_location(line: str) -> bool:
        """Heuristically detect location lines."""
        normalized = line.strip()
        if len(normalized.split()) == 1 and normalized[0].isalpha():
            return True
        location_keywords = {"street", "str", "road", "rd", "avenue", "ave", "city"}
        lowered = normalized.lower()
        return any(keyword in lowered for keyword in location_keywords)
