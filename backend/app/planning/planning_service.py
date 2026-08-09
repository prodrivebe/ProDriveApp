"""Planning board and loading optimization orchestration."""

from __future__ import annotations

import json
import uuid
from datetime import date

from sqlalchemy.orm import Session

from app.ai.audit_repository import AIAuditRepository
from app.ai.models.ai_suggestion import AISuggestion
from app.ai.repository import AISuggestionRepository
from app.common.enums import (
    AISuggestionStatus,
    AISuggestionType,
    LoadingPlanStatus,
    OrderStatus,
)
from app.common.exceptions import NotFoundError, ValidationError
from app.drivers.repository import DriverRepository
from app.fleet.assignment_repository import FleetAssignmentRepository
from app.orders.models import Order
from app.orders.repository import OrderRepository
from app.orders.schemas import AssignDriverRequest
from app.orders.service import OrderService
from app.planning.capacity_validator import CapacityValidator
from app.planning.loading_optimizer import (
    DEFAULT_VEHICLE_HEIGHT_M,
    DEFAULT_VEHICLE_WEIGHT_KG,
    LoadingOptimizer,
    PositionRecommendation,
    VehicleLoadInput,
)
from app.planning.repository import LoadingPlanRepository
from app.planning.route_planner import RoutePlanner
from app.planning.schemas import (
    LoadPlanRequest,
    LoadPlanResponse,
    LoadingPositionInput,
    LoadingPositionResponse,
    OptimizationResponse,
    PlanningAssignRequest,
    PlanningBoardQuery,
    PlanningBoardResponse,
    PlanningOrderCard,
    ResourceAvailability,
    ValidateRequest,
    ValidationResponse,
)
from app.trailers.repository import TrailerRepository
from app.trucks.repository import TruckRepository
from app.users.models import User
from app.users.repository import UserRepository

PLANNING_COLUMNS: dict[str, set[str]] = {
    "unassigned": {OrderStatus.DRAFT.value, OrderStatus.READY.value},
    "planned": {OrderStatus.READY.value},
    "assigned": {OrderStatus.ASSIGNED.value},
    "loading": {
        OrderStatus.ACCEPTED.value,
        OrderStatus.ARRIVED_PICKUP.value,
        OrderStatus.LOADING.value,
        OrderStatus.LOADED.value,
    },
    "in_transit": {OrderStatus.IN_TRANSIT.value, OrderStatus.ARRIVED_DELIVERY.value},
    "delivering": {OrderStatus.DELIVERING.value},
    "completed": {OrderStatus.COMPLETED.value},
}


class PlanningService:
    """Planning board, assignments, and loading optimization."""

    def __init__(self, db: Session) -> None:
        self._db = db
        self._orders = OrderService(db)
        self._order_repo = OrderRepository(db)
        self._drivers = DriverRepository(db)
        self._trucks = TruckRepository(db)
        self._trailers = TrailerRepository(db)
        self._users = UserRepository(db)
        self._fleet_assignments = FleetAssignmentRepository(db)
        self._loading_plans = LoadingPlanRepository(db)
        self._suggestions = AISuggestionRepository(db)
        self._audit = AIAuditRepository(db)
        self._optimizer = LoadingOptimizer()
        self._validator = CapacityValidator()
        self._route_planner = RoutePlanner()

    def get_board(self, current_user: User, query: PlanningBoardQuery) -> PlanningBoardResponse:
        """Return planning board columns and resource availability."""
        orders, _ = self._order_repo.list_for_company(
            current_user.company_id,
            page=1,
            page_size=300,
            search=query.search,
            driver_id=query.driver_id,
        )
        active_orders = [
            order
            for order in orders
            if OrderStatus(order.status) not in {OrderStatus.CANCELLED}
        ]
        if query.planned_date:
            active_orders = [
                order
                for order in active_orders
                if order.planned_pickup_date == query.planned_date
                or order.planned_delivery_date == query.planned_date
            ]
        if query.truck_id:
            active_orders = [order for order in active_orders if order.assigned_truck_id == query.truck_id]
        if query.trailer_id:
            active_orders = [
                order for order in active_orders if order.assigned_trailer_id == query.trailer_id
            ]

        columns: dict[str, list[PlanningOrderCard]] = {key: [] for key in PLANNING_COLUMNS}
        for order in active_orders:
            column = self._resolve_column(order)
            columns[column].append(self._to_order_card(order, column))

        drivers, _ = self._drivers.list_for_company(
            current_user.company_id,
            page=1,
            page_size=100,
            active=True,
            search=None,
        )
        trucks, _ = self._trucks.list_for_company(
            current_user.company_id,
            page=1,
            page_size=100,
            active=True,
            search=None,
        )
        trailers, _ = self._trailers.list_for_company(
            current_user.company_id,
            page=1,
            page_size=100,
            active=True,
            search=None,
        )
        active_assignments = self._fleet_assignments.list_for_company(
            current_user.company_id,
            active_only=True,
        )

        driver_resources = [
            self._resource_for_driver(driver, active_orders, active_assignments)
            for driver in drivers
        ]
        truck_resources = [
            self._resource_for_truck(truck, active_orders) for truck in trucks
        ]
        trailer_resources = [
            self._resource_for_trailer(trailer, active_orders) for trailer in trailers
        ]

        assignment_payload = [
            {
                "id": str(item.id),
                "driver_id": str(item.driver_id),
                "truck_id": str(item.truck_id) if item.truck_id else None,
                "trailer_id": str(item.trailer_id) if item.trailer_id else None,
                "order_id": str(item.order_id) if item.order_id else None,
                "active": item.active,
            }
            for item in active_assignments
        ]

        return PlanningBoardResponse(
            columns=columns,
            drivers=driver_resources,
            trucks=truck_resources,
            trailers=trailer_resources,
            active_assignments=assignment_payload,
        )

    def assign(self, current_user: User, payload: PlanningAssignRequest, ip_address: str | None) -> Order:
        """Assign, reassign, or clear fleet resources on an order."""
        order = self._orders.get_order(current_user, payload.order_id)
        if payload.clear_assignment:
            if OrderStatus(order.status) != OrderStatus.ASSIGNED:
                raise ValidationError(
                    code="CANNOT_CLEAR_ASSIGNMENT",
                    message="Only assigned orders can be unassigned from the planning board.",
                )
            updated = self._order_repo.update_status(
                order,
                OrderStatus.READY,
                current_user.id,
                clear_assignment=True,
            )
            self._orders.record_timeline_event(
                current_user,
                order.id,
                "ASSIGNMENT_CHANGED",
                "Assignment cleared from planning board.",
            )
            return self._orders.get_order(current_user, updated.id)

        if payload.driver_id is None:
            raise ValidationError(code="DRIVER_REQUIRED", message="driver_id is required to assign.")
        return self._orders.assign_driver(
            current_user,
            payload.order_id,
            AssignDriverRequest(
                driver_id=payload.driver_id,
                truck_id=payload.truck_id,
                trailer_id=payload.trailer_id,
            ),
            ip_address=ip_address,
        )

    def optimize(
        self,
        current_user: User,
        order_id: uuid.UUID,
        *,
        include_route: bool = True,
    ) -> OptimizationResponse:
        """Generate loading/route optimization as a pending AI suggestion."""
        order = self._orders.get_order(current_user, order_id)
        loading_result, route_result, validation = self._build_optimization(order)
        output_json = {
            "order_id": str(order.id),
            "loading": loading_result.to_output_json(),
            "route": route_result.to_output_json() if route_result else None,
            "validation": validation.to_dict(),
        }
        suggestion = self._suggestions.create(
            company_id=current_user.company_id,
            suggestion_type=AISuggestionType.LOADING_OPTIMIZATION,
            input_text=f"order_id={order.id}",
            output_json=output_json,
            confidence=loading_result.confidence,
            prompt_version=LoadingOptimizer.PROMPT_VERSION,
            model_version=LoadingOptimizer.MODEL_VERSION,
            created_by=current_user.id,
            related_order_id=order.id,
        )
        self._audit.create(
            company_id=current_user.company_id,
            user_id=current_user.id,
            event_type="REQUEST",
            prompt_version=LoadingOptimizer.PROMPT_VERSION,
            model_version=LoadingOptimizer.MODEL_VERSION,
            input_text=f"order_id={order.id}",
            suggestion_id=suggestion.id,
        )
        self._audit.create(
            company_id=current_user.company_id,
            user_id=current_user.id,
            event_type="RESPONSE",
            prompt_version=LoadingOptimizer.PROMPT_VERSION,
            model_version=LoadingOptimizer.MODEL_VERSION,
            output_json=output_json,
            confidence=loading_result.confidence,
            suggestion_id=suggestion.id,
        )
        self._orders.record_timeline_event(
            current_user,
            order.id,
            "LOADING_PLAN_OPTIMIZED",
            "Loading optimization recommendation generated.",
        )
        reasoning = loading_result.reasoning + (route_result.reasoning if route_result else [])
        return OptimizationResponse(
            suggestion_id=suggestion.id,
            order_id=order.id,
            loading=loading_result.to_output_json(),
            route=route_result.to_output_json() if route_result else None,
            validation=validation.to_dict(),
            confidence=loading_result.confidence,
            reasoning=reasoning,
            status=AISuggestionStatus.PENDING.value,
        )

    def validate_plan(
        self,
        current_user: User,
        payload: ValidateRequest,
    ) -> ValidationResponse:
        """Validate draft or persisted loading positions."""
        order = self._orders.get_order(current_user, payload.order_id)
        trailer = self._resolve_trailer(order)
        positions = self._inputs_to_recommendations(payload.positions, order)
        vehicle_weights, vehicle_heights = self._vehicle_metrics(order)
        result = self._validator.validate(
            trailer_capacity=trailer.maximum_vehicle_count if trailer else len(positions),
            trailer_max_height_m=float(trailer.maximum_height) if trailer and trailer.maximum_height else None,
            trailer_max_weight_kg=float(trailer.maximum_weight) if trailer and trailer.maximum_weight else None,
            trailer_type=trailer.trailer_type if trailer else None,
            positions=positions,
            vehicle_weights=vehicle_weights,
            vehicle_heights=vehicle_heights,
            unloading_sequence=payload.route_sequence,
        )
        return ValidationResponse(**result.to_dict())

    def save_load_plan(
        self,
        current_user: User,
        payload: LoadPlanRequest,
        ip_address: str | None,
    ) -> LoadPlanResponse:
        """Save draft loading plan or confirm an approved/manual plan."""
        order = self._orders.get_order(current_user, payload.order_id)
        if payload.confirm:
            if payload.suggestion_id:
                suggestion = self._suggestions.get_by_id_for_company(
                    payload.suggestion_id,
                    current_user.company_id,
                )
                if suggestion is None or suggestion.status != AISuggestionStatus.APPROVED.value:
                    raise ValidationError(
                        code="SUGGESTION_NOT_APPROVED",
                        message="Loading plan confirmation requires an approved AI suggestion.",
                    )
                output = json.loads(suggestion.output_json)
                positions_raw = output.get("loading", {}).get("positions", [])
                positions = [item for item in positions_raw if isinstance(item, dict)]
                route_data = output.get("route")
                route_sequence = (
                    [uuid.UUID(str(item["stop_id"])) for item in route_data.get("stops", [])]
                    if isinstance(route_data, dict)
                    else None
                )
                ai_generated = True
            else:
                positions = [item.model_dump() for item in payload.positions]
                route_sequence = payload.route_sequence
                ai_generated = False
                validation = self.validate_plan(
                    current_user,
                    ValidateRequest(order_id=payload.order_id, positions=payload.positions),
                )
                if not validation.is_valid:
                    raise ValidationError(
                        code="VALIDATION_FAILED",
                        message="Loading plan failed validation.",
                    )
                if validation.warnings and not payload.acknowledge_warnings:
                    raise ValidationError(
                        code="WARNINGS_NOT_ACKNOWLEDGED",
                        message="Acknowledge capacity warnings before confirming the loading plan.",
                    )

            plan = self._persist_plan(
                current_user,
                order,
                positions,
                route_sequence,
                confirmed=True,
                ai_generated=ai_generated,
            )
            self._orders.record_timeline_event(
                current_user,
                order.id,
                "LOADING_PLAN_UPDATED" if ai_generated else "LOADING_PLAN_CREATED",
                "Loading plan confirmed by dispatcher.",
            )
            return self._to_load_plan_response(plan, order)

        positions = [item.model_dump() for item in payload.positions]
        existing = self._loading_plans.get_by_order_for_company(order.id, current_user.company_id)
        if existing and existing.status == LoadingPlanStatus.DRAFT.value:
            plan = self._loading_plans.replace_positions(
                existing,
                positions,
                confirmed=False,
                updated_by=current_user.id,
            )
        else:
            plan = self._loading_plans.create(
                company_id=current_user.company_id,
                order_id=order.id,
                trailer_id=order.assigned_trailer_id,
                status=LoadingPlanStatus.DRAFT,
                route_sequence_json={"stop_ids": [str(item) for item in (payload.route_sequence or [])]},
                estimated_total_height=None,
                estimated_total_weight=None,
                estimated_travel_km=None,
                front_axle_percent=None,
                rear_axle_percent=None,
                validation_warnings=None,
                ai_generated=False,
                created_by=current_user.id,
            )
            plan = self._loading_plans.replace_positions(
                plan,
                positions,
                confirmed=False,
                updated_by=current_user.id,
            )
        self._orders.record_timeline_event(
            current_user,
            order.id,
            "LOADING_PLAN_CREATED",
            "Loading plan draft saved.",
        )
        return self._to_load_plan_response(plan, order)

    def get_load_plan(self, current_user: User, order_id: uuid.UUID) -> LoadPlanResponse:
        """Return the latest loading plan for an order."""
        order = self._orders.get_order(current_user, order_id)
        plan = self._loading_plans.get_by_order_for_company(order_id, current_user.company_id)
        if plan is None:
            raise NotFoundError(code="LOAD_PLAN_NOT_FOUND", message="Loading plan not found.")
        return self._to_load_plan_response(plan, order)

    def apply_loading_suggestion(
        self,
        current_user: User,
        suggestion: AISuggestion,
        output: dict[str, object],
    ) -> LoadingPlan:
        """Persist an approved loading optimization suggestion."""
        order_id = suggestion.related_order_id
        if order_id is None:
            raise ValidationError(code="ORDER_REQUIRED", message="Suggestion must reference an order.")
        order = self._orders.get_order(current_user, order_id)
        loading = output.get("loading", {})
        positions = loading.get("positions", []) if isinstance(loading, dict) else []
        route = output.get("route")
        route_sequence = None
        if isinstance(route, dict):
            route_sequence = [
                uuid.UUID(str(item["stop_id"]))
                for item in route.get("stops", [])
                if isinstance(item, dict)
            ]
        return self._persist_plan(
            current_user,
            order,
            [item for item in positions if isinstance(item, dict)],
            route_sequence,
            confirmed=True,
            ai_generated=True,
        )

    def _persist_plan(
        self,
        current_user: User,
        order: Order,
        positions: list[dict[str, object]],
        route_sequence: list[uuid.UUID] | None,
        *,
        confirmed: bool,
        ai_generated: bool,
    ) -> LoadingPlan:
        validation = self._validator.validate(
            trailer_capacity=self._resolve_trailer(order).maximum_vehicle_count
            if self._resolve_trailer(order)
            else len(positions),
            trailer_max_height_m=float(self._resolve_trailer(order).maximum_height)
            if self._resolve_trailer(order) and self._resolve_trailer(order).maximum_height
            else None,
            trailer_max_weight_kg=float(self._resolve_trailer(order).maximum_weight)
            if self._resolve_trailer(order) and self._resolve_trailer(order).maximum_weight
            else None,
            trailer_type=self._resolve_trailer(order).trailer_type if self._resolve_trailer(order) else None,
            positions=self._dicts_to_recommendations(positions),
            vehicle_weights=self._vehicle_metrics(order)[0],
            vehicle_heights=self._vehicle_metrics(order)[1],
            unloading_sequence=route_sequence,
        )
        existing = self._loading_plans.get_by_order_for_company(order.id, current_user.company_id)
        route_json = {"stop_ids": [str(item) for item in (route_sequence or [])]}
        if existing:
            existing.route_sequence_json = json.dumps(route_json)
            existing.estimated_total_height = validation.estimated_total_height_m
            existing.estimated_total_weight = validation.estimated_total_weight_kg
            existing.front_axle_percent = validation.front_axle_percent
            existing.rear_axle_percent = validation.rear_axle_percent
            existing.validation_warnings_json = json.dumps(
                [item.message for item in validation.warnings]
            )
            existing.ai_generated = ai_generated
            return self._loading_plans.replace_positions(
                existing,
                positions,
                confirmed=confirmed,
                updated_by=current_user.id,
            )
        plan = self._loading_plans.create(
            company_id=current_user.company_id,
            order_id=order.id,
            trailer_id=order.assigned_trailer_id,
            status=LoadingPlanStatus.CONFIRMED if confirmed else LoadingPlanStatus.DRAFT,
            route_sequence_json=route_json,
            estimated_total_height=validation.estimated_total_height_m,
            estimated_total_weight=validation.estimated_total_weight_kg,
            estimated_travel_km=None,
            front_axle_percent=validation.front_axle_percent,
            rear_axle_percent=validation.rear_axle_percent,
            validation_warnings=[item.message for item in validation.warnings],
            ai_generated=ai_generated,
            created_by=current_user.id,
        )
        return self._loading_plans.replace_positions(
            plan,
            positions,
            confirmed=confirmed,
            updated_by=current_user.id,
        )

    def _build_optimization(self, order: Order):
        trailer = self._resolve_trailer(order)
        vehicles = self._vehicle_inputs(order)
        loading_result = self._optimizer.optimize(
            trailer_capacity=trailer.maximum_vehicle_count if trailer else max(len(vehicles), 1),
            trailer_max_height_m=float(trailer.maximum_height) if trailer and trailer.maximum_height else None,
            trailer_max_weight_kg=float(trailer.maximum_weight) if trailer and trailer.maximum_weight else None,
            vehicles=vehicles,
        )
        route_result = self._route_planner.plan(order.stops)
        validation = self._validator.validate(
            trailer_capacity=trailer.maximum_vehicle_count if trailer else len(loading_result.positions),
            trailer_max_height_m=float(trailer.maximum_height) if trailer and trailer.maximum_height else None,
            trailer_max_weight_kg=float(trailer.maximum_weight) if trailer and trailer.maximum_weight else None,
            trailer_type=trailer.trailer_type if trailer else None,
            positions=loading_result.positions,
            vehicle_weights={item.vehicle_id: item.weight_kg for item in vehicles},
            vehicle_heights={item.vehicle_id: item.height_m for item in vehicles},
            unloading_sequence=loading_result.unloading_sequence,
        )
        return loading_result, route_result, validation

    def _vehicle_inputs(self, order: Order) -> list[VehicleLoadInput]:
        stops = [stop for stop in order.stops if stop.deleted_at is None]
        pickup_rank = {
            stop.id: stop.sequence
            for stop in stops
            if stop.stop_type == "PICKUP"
        }
        delivery_rank = {
            stop.id: stop.sequence
            for stop in stops
            if stop.stop_type == "DELIVERY"
        }
        vehicles: list[VehicleLoadInput] = []
        for vehicle in [item for item in order.vehicles if item.deleted_at is None]:
            delivery_stop = next(
                (stop for stop in stops if stop.id == vehicle.delivery_stop_id),
                None,
            )
            vehicles.append(
                VehicleLoadInput(
                    vehicle_id=vehicle.id,
                    make=vehicle.make,
                    model=vehicle.model,
                    weight_kg=float(vehicle.estimated_weight or DEFAULT_VEHICLE_WEIGHT_KG),
                    height_m=float(vehicle.estimated_height or DEFAULT_VEHICLE_HEIGHT_M),
                    pickup_sequence=pickup_rank.get(vehicle.pickup_stop_id, 1),
                    delivery_sequence=delivery_rank.get(vehicle.delivery_stop_id, 1),
                    destination_city=delivery_stop.city if delivery_stop else None,
                )
            )
        return vehicles

    def _resolve_trailer(self, order: Order):
        if order.assigned_trailer_id is None:
            return None
        return self._trailers.get_by_id_for_company(order.assigned_trailer_id, order.company_id)

    @staticmethod
    def _resolve_column(order: Order) -> str:
        status = OrderStatus(order.status)
        if status == OrderStatus.COMPLETED:
            return "completed"
        if status == OrderStatus.DELIVERING:
            return "delivering"
        if status in {OrderStatus.IN_TRANSIT, OrderStatus.ARRIVED_DELIVERY}:
            return "in_transit"
        if status in {
            OrderStatus.ACCEPTED,
            OrderStatus.ARRIVED_PICKUP,
            OrderStatus.LOADING,
            OrderStatus.LOADED,
        }:
            return "loading"
        if status == OrderStatus.ASSIGNED:
            return "assigned"
        if status == OrderStatus.READY and order.planned_pickup_date:
            return "planned"
        return "unassigned"

    @staticmethod
    def _to_order_card(order: Order, column: str) -> PlanningOrderCard:
        vehicle_count = len([vehicle for vehicle in order.vehicles if vehicle.deleted_at is None])
        return PlanningOrderCard(
            id=order.id,
            order_number=order.order_number,
            status=order.status,
            customer_id=order.customer_id,
            assigned_driver_id=order.assigned_driver_id,
            assigned_truck_id=order.assigned_truck_id,
            assigned_trailer_id=order.assigned_trailer_id,
            planned_pickup_date=order.planned_pickup_date,
            planned_delivery_date=order.planned_delivery_date,
            vehicle_count=vehicle_count,
            column=column,
        )

    def _resource_for_driver(self, driver, active_orders, active_assignments) -> ResourceAvailability:
        user = self._users.get_by_id(driver.user_id) if driver.user_id else None
        label = f"{user.first_name} {user.last_name}" if user else str(driver.id)[:8]
        active_count = len(
            [
                order
                for order in active_orders
                if order.assigned_driver_id == driver.id
                and OrderStatus(order.status) not in {OrderStatus.COMPLETED, OrderStatus.CANCELLED}
            ]
        )
        conflict = active_count > 1
        return ResourceAvailability(
            id=driver.id,
            label=label.strip(),
            resource_type="driver",
            available=active_count == 0,
            active_assignments=active_count,
            capacity_indicator=f"{active_count} active",
            conflict=conflict,
            conflict_reason="Multiple active orders assigned" if conflict else None,
        )

    def _resource_for_truck(self, truck, active_orders) -> ResourceAvailability:
        active_count = len(
            [
                order
                for order in active_orders
                if order.assigned_truck_id == truck.id
                and OrderStatus(order.status) not in {OrderStatus.COMPLETED, OrderStatus.CANCELLED}
            ]
        )
        return ResourceAvailability(
            id=truck.id,
            label=truck.registration_number,
            resource_type="truck",
            available=active_count == 0,
            active_assignments=active_count,
            conflict=active_count > 1,
            conflict_reason="Truck assigned to multiple active orders" if active_count > 1 else None,
        )

    def _resource_for_trailer(self, trailer, active_orders) -> ResourceAvailability:
        active_count = len(
            [
                order
                for order in active_orders
                if order.assigned_trailer_id == trailer.id
                and OrderStatus(order.status) not in {OrderStatus.COMPLETED, OrderStatus.CANCELLED}
            ]
        )
        return ResourceAvailability(
            id=trailer.id,
            label=trailer.registration_number,
            resource_type="trailer",
            available=active_count == 0,
            active_assignments=active_count,
            capacity_indicator=f"{trailer.maximum_vehicle_count} vehicles max",
            conflict=active_count > 1,
            conflict_reason="Trailer assigned to multiple active orders" if active_count > 1 else None,
        )

    def _inputs_to_recommendations(
        self,
        inputs: list[LoadingPositionInput],
        order: Order,
    ) -> list[PositionRecommendation]:
        labels = {
            vehicle.id: " ".join(part for part in [vehicle.make, vehicle.model] if part).strip()
            for vehicle in order.vehicles
        }
        return [
            PositionRecommendation(
                vehicle_id=item.vehicle_id,
                vehicle_label=labels.get(item.vehicle_id, str(item.vehicle_id)[:8]),
                upper_deck=item.upper_deck,
                trailer_position=item.trailer_position,
                loading_order=item.loading_order,
                unloading_order=item.unloading_order,
                destination_city=item.destination_city,
            )
            for item in inputs
        ]

    @staticmethod
    def _dicts_to_recommendations(items: list[dict[str, object]]) -> list[PositionRecommendation]:
        return [
            PositionRecommendation(
                vehicle_id=uuid.UUID(str(item["vehicle_id"])),
                vehicle_label=str(item.get("vehicle_label", item["vehicle_id"])),
                upper_deck=bool(item.get("upper_deck", False)),
                trailer_position=int(item["trailer_position"]),
                loading_order=int(item["loading_order"]),
                unloading_order=int(item["unloading_order"]),
                destination_city=item.get("destination_city"),
            )
            for item in items
        ]

    @staticmethod
    def _vehicle_metrics(order: Order) -> tuple[dict[uuid.UUID, float], dict[uuid.UUID, float]]:
        weights: dict[uuid.UUID, float] = {}
        heights: dict[uuid.UUID, float] = {}
        for vehicle in order.vehicles:
            if vehicle.deleted_at is not None:
                continue
            weights[vehicle.id] = float(vehicle.estimated_weight or DEFAULT_VEHICLE_WEIGHT_KG)
            heights[vehicle.id] = float(vehicle.estimated_height or DEFAULT_VEHICLE_HEIGHT_M)
        return weights, heights

    def _to_load_plan_response(self, plan, order: Order) -> LoadPlanResponse:
        warnings = json.loads(plan.validation_warnings_json or "[]")
        route_sequence: list[uuid.UUID] = []
        if plan.route_sequence_json:
            route_data = json.loads(plan.route_sequence_json)
            route_sequence = [uuid.UUID(item) for item in route_data.get("stop_ids", [])]
        labels = {
            vehicle.id: " ".join(part for part in [vehicle.make, vehicle.model] if part).strip()
            for vehicle in order.vehicles
        }
        weights, heights = self._vehicle_metrics(order)
        positions = [
            LoadingPositionResponse(
                vehicle_id=position.vehicle_id,
                vehicle_label=labels.get(position.vehicle_id),
                upper_deck=position.upper_deck,
                trailer_position=position.trailer_position,
                loading_order=position.loading_order,
                unloading_order=position.unloading_order,
                destination_city=position.destination_city,
                weight_kg=weights.get(position.vehicle_id),
                height_m=heights.get(position.vehicle_id),
                confirmed_by_dispatcher=position.confirmed_by_dispatcher,
                ai_generated=position.ai_generated,
            )
            for position in plan.positions
        ]
        return LoadPlanResponse(
            id=plan.id,
            order_id=plan.order_id,
            trailer_id=plan.trailer_id,
            status=plan.status,
            estimated_total_height=float(plan.estimated_total_height)
            if plan.estimated_total_height is not None
            else None,
            estimated_total_weight=float(plan.estimated_total_weight)
            if plan.estimated_total_weight is not None
            else None,
            estimated_travel_km=float(plan.estimated_travel_km)
            if plan.estimated_travel_km is not None
            else None,
            front_axle_percent=float(plan.front_axle_percent)
            if plan.front_axle_percent is not None
            else None,
            rear_axle_percent=float(plan.rear_axle_percent)
            if plan.rear_axle_percent is not None
            else None,
            warnings=warnings,
            positions=positions,
            route_sequence=route_sequence,
            created_at=plan.created_at,
            confirmed_at=plan.confirmed_at,
        )
