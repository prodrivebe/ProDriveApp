"""AI suggestion approval workflow."""

from __future__ import annotations

import json
import uuid
from datetime import date

from sqlalchemy.orm import Session

from app.ai.agents.driver_recommendation import DriverRecommendationAgent
from app.ai.agents.order_parser import OrderParserAgent
from app.ai.audit_repository import AIAuditRepository
from app.ai.models.ai_suggestion import AISuggestion
from app.ai.repository import AISuggestionRepository
from app.common.enums import AISuggestionStatus, AISuggestionType
from app.common.exceptions import NotFoundError, ValidationError
from app.orders.schemas import OrderCreateRequest, OrderStopCreateRequest, OrderVehicleCreateRequest
from app.orders.service import OrderService
from app.users.models import User


class SuggestionService:
    """Manage AI suggestion lifecycle and human approval."""

    def __init__(self, db: Session) -> None:
        self._db = db
        self._suggestions = AISuggestionRepository(db)
        self._audit = AIAuditRepository(db)
        self._orders = OrderService(db)
        self._order_parser = OrderParserAgent()
        self._driver_agent = DriverRecommendationAgent(db)

    def create_order_parse_suggestion(self, current_user: User, message: str) -> AISuggestion:
        """Run order parser agent and persist a pending suggestion."""
        parsed = self._order_parser.parse(message)
        output_json = parsed.to_output_json()
        suggestion = self._suggestions.create(
            company_id=current_user.company_id,
            suggestion_type=AISuggestionType.ORDER_PARSE,
            input_text=message,
            output_json=output_json,
            confidence=parsed.overall_confidence,
            prompt_version=self._order_parser.prompt_version,
            model_version=self._order_parser.model_version,
            created_by=current_user.id,
        )
        self._audit.create(
            company_id=current_user.company_id,
            user_id=current_user.id,
            event_type="REQUEST",
            prompt_version=self._order_parser.prompt_version,
            model_version=self._order_parser.model_version,
            input_text=message,
            suggestion_id=suggestion.id,
        )
        self._audit.create(
            company_id=current_user.company_id,
            user_id=current_user.id,
            event_type="RESPONSE",
            prompt_version=self._order_parser.prompt_version,
            model_version=self._order_parser.model_version,
            output_json=output_json,
            confidence=parsed.overall_confidence,
            suggestion_id=suggestion.id,
        )
        return suggestion

    def create_driver_recommendation_suggestion(
        self,
        current_user: User,
        order_id: uuid.UUID,
    ) -> AISuggestion:
        """Run driver recommendation agent and persist a pending suggestion."""
        order = self._orders.get_order(current_user, order_id)
        result = self._driver_agent.recommend(current_user.company_id, order)
        output_json = result.to_output_json()
        suggestion = self._suggestions.create(
            company_id=current_user.company_id,
            suggestion_type=AISuggestionType.DRIVER_RECOMMENDATION,
            input_text=f"order_id={order_id}",
            output_json=output_json,
            confidence=result.overall_confidence,
            prompt_version=self._driver_agent.prompt_version,
            model_version=self._driver_agent.model_version,
            created_by=current_user.id,
            related_order_id=order_id,
        )
        self._audit.create(
            company_id=current_user.company_id,
            user_id=current_user.id,
            event_type="REQUEST",
            prompt_version=self._driver_agent.prompt_version,
            model_version=self._driver_agent.model_version,
            input_text=f"order_id={order_id}",
            suggestion_id=suggestion.id,
        )
        self._audit.create(
            company_id=current_user.company_id,
            user_id=current_user.id,
            event_type="RESPONSE",
            prompt_version=self._driver_agent.prompt_version,
            model_version=self._driver_agent.model_version,
            output_json=output_json,
            confidence=result.overall_confidence,
            suggestion_id=suggestion.id,
        )
        return suggestion

    def list_suggestions(
        self,
        current_user: User,
        *,
        status: AISuggestionStatus | None = None,
        suggestion_type: AISuggestionType | None = None,
    ) -> list[AISuggestion]:
        return self._suggestions.list_for_company(
            current_user.company_id,
            status=status,
            suggestion_type=suggestion_type,
        )

    def get_suggestion(self, current_user: User, suggestion_id: uuid.UUID) -> AISuggestion:
        suggestion = self._suggestions.get_by_id_for_company(suggestion_id, current_user.company_id)
        if suggestion is None:
            raise NotFoundError(code="SUGGESTION_NOT_FOUND", message="AI suggestion not found.")
        return suggestion

    def approve_suggestion(
        self,
        current_user: User,
        suggestion_id: uuid.UUID,
        *,
        customer_id: uuid.UUID | None = None,
        edited_output: dict[str, object] | None = None,
        ip_address: str | None = None,
    ) -> AISuggestion:
        suggestion = self.get_suggestion(current_user, suggestion_id)
        if suggestion.status != AISuggestionStatus.PENDING.value:
            raise ValidationError(
                code="SUGGESTION_NOT_PENDING",
                message="Only pending suggestions can be approved.",
            )

        output = json.loads(suggestion.output_json)
        if edited_output:
            output.update(edited_output)

        related_order_id = suggestion.related_order_id
        if suggestion.suggestion_type == AISuggestionType.ORDER_PARSE.value:
            if customer_id is None:
                raise ValidationError(
                    code="CUSTOMER_REQUIRED",
                    message="customer_id is required to approve an order parse suggestion.",
                )
            order = self._create_order_from_output(
                current_user,
                customer_id=customer_id,
                output=output,
                ip_address=ip_address,
            )
            related_order_id = order.id
            output["created_order_id"] = str(order.id)
        elif suggestion.suggestion_type == AISuggestionType.LOADING_OPTIMIZATION.value:
            from app.planning.planning_service import PlanningService

            planning = PlanningService(self._db)
            plan = planning.apply_loading_suggestion(current_user, suggestion, output)
            output["loading_plan_id"] = str(plan.id)
            if suggestion.related_order_id is not None:
                self._orders.record_timeline_event(
                    current_user,
                    suggestion.related_order_id,
                    "OPTIMIZATION_APPLIED",
                    "Loading optimization approved and applied.",
                )

        updated = self._suggestions.update_status(
            suggestion,
            status=AISuggestionStatus.APPROVED,
            approved_by=current_user.id,
            output_json=output,
            related_order_id=related_order_id,
        )
        self._audit.create(
            company_id=current_user.company_id,
            user_id=current_user.id,
            event_type="APPROVED",
            prompt_version=suggestion.prompt_version,
            model_version=suggestion.model_version,
            output_json=output,
            confidence=suggestion.confidence,
            dispatcher_decision=AISuggestionStatus.APPROVED.value,
            suggestion_id=suggestion.id,
        )
        return updated

    def reject_suggestion(
        self,
        current_user: User,
        suggestion_id: uuid.UUID,
        *,
        reason: str | None = None,
    ) -> AISuggestion:
        suggestion = self.get_suggestion(current_user, suggestion_id)
        if suggestion.status != AISuggestionStatus.PENDING.value:
            raise ValidationError(
                code="SUGGESTION_NOT_PENDING",
                message="Only pending suggestions can be rejected.",
            )
        output = json.loads(suggestion.output_json)
        if reason:
            output["rejection_reason"] = reason
        updated = self._suggestions.update_status(
            suggestion,
            status=AISuggestionStatus.REJECTED,
            approved_by=current_user.id,
            output_json=output,
        )
        self._audit.create(
            company_id=current_user.company_id,
            user_id=current_user.id,
            event_type="REJECTED",
            prompt_version=suggestion.prompt_version,
            model_version=suggestion.model_version,
            output_json=output,
            dispatcher_decision=AISuggestionStatus.REJECTED.value,
            suggestion_id=suggestion.id,
        )
        return updated

    def _create_order_from_output(
        self,
        current_user: User,
        *,
        customer_id: uuid.UUID,
        output: dict[str, object],
        ip_address: str | None,
    ):
        pickup_raw = output.get("pickup_stops", [])
        delivery_raw = output.get("delivery_stops", [])
        vehicles_raw = output.get("vehicles", [])
        stops: list[OrderStopCreateRequest] = []
        for index, raw in enumerate([*(pickup_raw if isinstance(pickup_raw, list) else []), *(delivery_raw if isinstance(delivery_raw, list) else [])], start=1):
            if not isinstance(raw, dict):
                continue
            raw = {**raw, "sequence": index}
            stops.append(OrderStopCreateRequest(**raw))
        vehicles = [
            OrderVehicleCreateRequest(**item)
            for item in vehicles_raw
            if isinstance(item, dict)
        ]

        pickup_date = output.get("planned_pickup_date")
        delivery_date = output.get("planned_delivery_date")
        payload = OrderCreateRequest(
            customer_id=customer_id,
            planned_pickup_date=date.fromisoformat(pickup_date) if isinstance(pickup_date, str) else None,
            planned_delivery_date=date.fromisoformat(delivery_date) if isinstance(delivery_date, str) else None,
            notes=output.get("notes") if isinstance(output.get("notes"), str) else None,
            stops=stops,
            vehicles=vehicles,
        )
        if not payload.stops:
            raise ValidationError(code="MISSING_STOPS", message="Approved suggestion must include stops.")
        if not payload.vehicles:
            raise ValidationError(code="MISSING_VEHICLES", message="Approved suggestion must include vehicles.")
        return self._orders.create_order(current_user, payload, ip_address=ip_address)
