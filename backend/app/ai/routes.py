"""AI API routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.ai.schemas import (
    OrderQualityResponse,
    OrderScopedRequest,
    ParseOrderRequest,
    ParsedOrderDraft,
    SuggestDriverResponse,
    SuggestEmptyKmResponse,
    SuggestLoadingResponse,
    SuggestRouteResponse,
)
from app.ai.service import AIService
from app.common.responses import SuccessResponse, success_response
from app.database.session import get_db
from app.orders.permissions import require_order_manager
from app.users.models import User

router = APIRouter(prefix="/ai", tags=["AI"])


def get_ai_service(db: Session = Depends(get_db)) -> AIService:
    """Provide an AI service instance."""
    return AIService(db)


@router.post("/parse-order", response_model=SuccessResponse[ParsedOrderDraft])
def parse_order(
    payload: ParseOrderRequest,
    current_user: User = Depends(require_order_manager),
    ai_service: AIService = Depends(get_ai_service),
) -> SuccessResponse[ParsedOrderDraft]:
    """Parse a customer message into a draft order structure."""
    _ = current_user
    draft = ai_service.parse_order(payload)
    return success_response(draft)


@router.post("/suggest-driver", response_model=SuccessResponse[SuggestDriverResponse])
def suggest_driver(
    payload: OrderScopedRequest,
    current_user: User = Depends(require_order_manager),
    ai_service: AIService = Depends(get_ai_service),
) -> SuccessResponse[SuggestDriverResponse]:
    """Suggest a driver for an order."""
    return success_response(ai_service.suggest_driver(current_user, payload))


@router.post("/suggest-route", response_model=SuccessResponse[SuggestRouteResponse])
def suggest_route(
    payload: OrderScopedRequest,
    current_user: User = Depends(require_order_manager),
    ai_service: AIService = Depends(get_ai_service),
) -> SuccessResponse[SuggestRouteResponse]:
    """Suggest a route order for an order."""
    return success_response(ai_service.suggest_route(current_user, payload))


@router.post("/suggest-loading", response_model=SuccessResponse[SuggestLoadingResponse])
def suggest_loading(
    payload: OrderScopedRequest,
    current_user: User = Depends(require_order_manager),
    ai_service: AIService = Depends(get_ai_service),
) -> SuccessResponse[SuggestLoadingResponse]:
    """Suggest trailer loading positions for an order."""
    return success_response(ai_service.suggest_loading(current_user, payload))


@router.post("/score-order", response_model=SuccessResponse[OrderQualityResponse])
def score_order(
    payload: OrderScopedRequest,
    current_user: User = Depends(require_order_manager),
    ai_service: AIService = Depends(get_ai_service),
) -> SuccessResponse[OrderQualityResponse]:
    """Score order completeness and quality."""
    return success_response(ai_service.score_order_quality(current_user, payload))


@router.post("/suggest-empty-km", response_model=SuccessResponse[SuggestEmptyKmResponse])
def suggest_empty_km(
    current_user: User = Depends(require_order_manager),
    ai_service: AIService = Depends(get_ai_service),
) -> SuccessResponse[SuggestEmptyKmResponse]:
    """Suggest ways to reduce empty kilometers."""
    return success_response(ai_service.suggest_empty_km(current_user))
