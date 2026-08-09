"""Legacy advisory AI helpers (route, loading, scoring)."""

from sqlalchemy.orm import Session

from app.ai.schemas import (
    EmptyKmSuggestion,
    OrderQualityResponse,
    OrderScopedRequest,
    RouteStopSuggestion,
    LoadingPositionSuggestion,
    SuggestEmptyKmResponse,
    SuggestLoadingResponse,
    SuggestRouteResponse,
)
from app.common.enums import OrderStatus, StopType
from app.drivers.repository import DriverRepository
from app.orders.repository import OrderRepository
from app.orders.service import OrderService
from app.users.models import User
from app.users.repository import UserRepository


class AIService:
    """Non-mutating advisory AI helpers outside the suggestion approval workflow."""

    def __init__(self, db: Session) -> None:
        self._db = db
        self._orders = OrderService(db)
        self._order_repo = OrderRepository(db)
        self._drivers = DriverRepository(db)
        self._users = UserRepository(db)

    def suggest_route(
        self,
        current_user: User,
        payload: OrderScopedRequest,
    ) -> SuggestRouteResponse:
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
