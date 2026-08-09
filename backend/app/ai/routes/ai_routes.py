"""AI API routes."""

from __future__ import annotations

import json
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.ai.schemas import (
    AISuggestionResponse,
    ApproveSuggestionRequest,
    OrderQualityResponse,
    OrderScopedRequest,
    ParseOrderSuggestionRequest,
    RecommendDriverRequest,
    RejectSuggestionRequest,
    SuggestEmptyKmResponse,
    SuggestLoadingResponse,
    SuggestRouteResponse,
)
from app.ai.services.ai_service import AIService
from app.ai.services.suggestion_service import SuggestionService
from app.common.enums import AISuggestionStatus, AISuggestionType
from app.common.responses import SuccessResponse, success_response
from app.database.session import get_db
from app.orders.permissions import require_order_manager
from app.users.models import User

router = APIRouter(prefix="/ai", tags=["AI"])


def get_ai_service(db: Session = Depends(get_db)) -> AIService:
    return AIService(db)


def get_suggestion_service(db: Session = Depends(get_db)) -> SuggestionService:
    return SuggestionService(db)


def _to_response(suggestion) -> AISuggestionResponse:
    return AISuggestionResponse(
        id=suggestion.id,
        company_id=suggestion.company_id,
        suggestion_type=suggestion.suggestion_type,
        input_text=suggestion.input_text,
        output_json=json.loads(suggestion.output_json),
        confidence=suggestion.confidence,
        status=suggestion.status,
        prompt_version=suggestion.prompt_version,
        model_version=suggestion.model_version,
        created_by=suggestion.created_by,
        approved_by=suggestion.approved_by,
        created_at=suggestion.created_at,
        approved_at=suggestion.approved_at,
        related_order_id=suggestion.related_order_id,
    )


@router.post("/parse-order", response_model=SuccessResponse[AISuggestionResponse])
def parse_order(
    payload: ParseOrderSuggestionRequest,
    current_user: User = Depends(require_order_manager),
    suggestion_service: SuggestionService = Depends(get_suggestion_service),
) -> SuccessResponse[AISuggestionResponse]:
    """Parse customer text into a pending AI order suggestion."""
    suggestion = suggestion_service.create_order_parse_suggestion(current_user, payload.message)
    return success_response(_to_response(suggestion))


@router.post("/recommend-driver", response_model=SuccessResponse[AISuggestionResponse])
def recommend_driver(
    payload: RecommendDriverRequest,
    current_user: User = Depends(require_order_manager),
    suggestion_service: SuggestionService = Depends(get_suggestion_service),
) -> SuccessResponse[AISuggestionResponse]:
    """Create a pending driver recommendation suggestion."""
    suggestion = suggestion_service.create_driver_recommendation_suggestion(
        current_user,
        payload.order_id,
    )
    return success_response(_to_response(suggestion))


@router.post("/suggest-driver", response_model=SuccessResponse[AISuggestionResponse])
def suggest_driver(
    payload: OrderScopedRequest,
    current_user: User = Depends(require_order_manager),
    suggestion_service: SuggestionService = Depends(get_suggestion_service),
) -> SuccessResponse[AISuggestionResponse]:
    """Backward-compatible alias for driver recommendation suggestions."""
    suggestion = suggestion_service.create_driver_recommendation_suggestion(
        current_user,
        payload.order_id,
    )
    return success_response(_to_response(suggestion))


@router.get("/suggestions", response_model=SuccessResponse[list[AISuggestionResponse]])
def list_suggestions(
    status: AISuggestionStatus | None = Query(default=None),
    suggestion_type: AISuggestionType | None = Query(default=None),
    current_user: User = Depends(require_order_manager),
    suggestion_service: SuggestionService = Depends(get_suggestion_service),
) -> SuccessResponse[list[AISuggestionResponse]]:
    suggestions = suggestion_service.list_suggestions(
        current_user,
        status=status,
        suggestion_type=suggestion_type,
    )
    return success_response([_to_response(item) for item in suggestions])


@router.get("/suggestions/{suggestion_id}", response_model=SuccessResponse[AISuggestionResponse])
def get_suggestion(
    suggestion_id: uuid.UUID,
    current_user: User = Depends(require_order_manager),
    suggestion_service: SuggestionService = Depends(get_suggestion_service),
) -> SuccessResponse[AISuggestionResponse]:
    suggestion = suggestion_service.get_suggestion(current_user, suggestion_id)
    return success_response(_to_response(suggestion))


@router.post("/suggestions/{suggestion_id}/approve", response_model=SuccessResponse[AISuggestionResponse])
def approve_suggestion(
    suggestion_id: uuid.UUID,
    payload: ApproveSuggestionRequest,
    current_user: User = Depends(require_order_manager),
    suggestion_service: SuggestionService = Depends(get_suggestion_service),
) -> SuccessResponse[AISuggestionResponse]:
    suggestion = suggestion_service.approve_suggestion(
        current_user,
        suggestion_id,
        customer_id=payload.customer_id,
        edited_output=payload.edited_output,
    )
    return success_response(_to_response(suggestion))


@router.post("/suggestions/{suggestion_id}/reject", response_model=SuccessResponse[AISuggestionResponse])
def reject_suggestion(
    suggestion_id: uuid.UUID,
    payload: RejectSuggestionRequest,
    current_user: User = Depends(require_order_manager),
    suggestion_service: SuggestionService = Depends(get_suggestion_service),
) -> SuccessResponse[AISuggestionResponse]:
    suggestion = suggestion_service.reject_suggestion(
        current_user,
        suggestion_id,
        reason=payload.reason,
    )
    return success_response(_to_response(suggestion))


@router.post("/suggest-route", response_model=SuccessResponse[SuggestRouteResponse])
def suggest_route(
    payload: OrderScopedRequest,
    current_user: User = Depends(require_order_manager),
    ai_service: AIService = Depends(get_ai_service),
) -> SuccessResponse[SuggestRouteResponse]:
    return success_response(ai_service.suggest_route(current_user, payload))


@router.post("/suggest-loading", response_model=SuccessResponse[SuggestLoadingResponse])
def suggest_loading(
    payload: OrderScopedRequest,
    current_user: User = Depends(require_order_manager),
    ai_service: AIService = Depends(get_ai_service),
) -> SuccessResponse[SuggestLoadingResponse]:
    return success_response(ai_service.suggest_loading(current_user, payload))


@router.post("/score-order", response_model=SuccessResponse[OrderQualityResponse])
def score_order(
    payload: OrderScopedRequest,
    current_user: User = Depends(require_order_manager),
    ai_service: AIService = Depends(get_ai_service),
) -> SuccessResponse[OrderQualityResponse]:
    return success_response(ai_service.score_order_quality(current_user, payload))


@router.post("/suggest-empty-km", response_model=SuccessResponse[SuggestEmptyKmResponse])
def suggest_empty_km(
    current_user: User = Depends(require_order_manager),
    ai_service: AIService = Depends(get_ai_service),
) -> SuccessResponse[SuggestEmptyKmResponse]:
    return success_response(ai_service.suggest_empty_km(current_user))
