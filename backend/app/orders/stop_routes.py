"""Standalone stop API routes."""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.responses import SuccessResponse, success_response
from app.database.session import get_db
from app.orders.permissions import require_order_manager
from app.orders.schemas import OrderStopResponse, OrderStopUpdateRequest
from app.orders.service import OrderService
from app.users.models import User

router = APIRouter(prefix="/stops", tags=["Stops"])


def get_order_service(db: Session = Depends(get_db)) -> OrderService:
    """Provide an order service instance."""
    return OrderService(db)


@router.put("/{stop_id}", response_model=SuccessResponse[OrderStopResponse])
def update_stop(
    stop_id: uuid.UUID,
    payload: OrderStopUpdateRequest,
    current_user: User = Depends(require_order_manager),
    order_service: OrderService = Depends(get_order_service),
) -> SuccessResponse[OrderStopResponse]:
    """Update a stop."""
    stop = order_service.update_stop(current_user, stop_id, payload)
    return success_response(OrderStopResponse.model_validate(stop))


@router.delete("/{stop_id}", response_model=SuccessResponse[dict[str, str]])
def delete_stop(
    stop_id: uuid.UUID,
    current_user: User = Depends(require_order_manager),
    order_service: OrderService = Depends(get_order_service),
) -> SuccessResponse[dict[str, str]]:
    """Soft delete a stop."""
    order_service.delete_stop(current_user, stop_id)
    return success_response({"message": "Stop deleted successfully."})
