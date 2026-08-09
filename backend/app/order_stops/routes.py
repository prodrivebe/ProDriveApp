"""Standalone order stop API routes."""

import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.common.responses import SuccessResponse, success_response
from app.database.session import get_db
from app.order_stops.permissions import require_order_manager
from app.order_stops.schemas import OrderStopResponse, OrderStopUpdateRequest
from app.order_stops.service import OrderStopService
from app.users.models import User

router = APIRouter(prefix="/stops", tags=["Stops"])


def get_client_ip(request: Request) -> str | None:
    """Extract the client IP address from the request."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip()
    if request.client is not None:
        return request.client.host
    return None


def get_order_stop_service(db: Session = Depends(get_db)) -> OrderStopService:
    """Provide an order stop service instance."""
    return OrderStopService(db)


@router.put("/{stop_id}", response_model=SuccessResponse[OrderStopResponse])
def update_stop(
    stop_id: uuid.UUID,
    payload: OrderStopUpdateRequest,
    request: Request,
    current_user: User = Depends(require_order_manager),
    stop_service: OrderStopService = Depends(get_order_stop_service),
) -> SuccessResponse[OrderStopResponse]:
    """Update a stop."""
    stop = stop_service.update_stop(
        current_user,
        stop_id,
        payload,
        get_client_ip(request),
    )
    return success_response(OrderStopResponse.model_validate(stop))


@router.delete("/{stop_id}", response_model=SuccessResponse[dict[str, str]])
def delete_stop(
    stop_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(require_order_manager),
    stop_service: OrderStopService = Depends(get_order_stop_service),
) -> SuccessResponse[dict[str, str]]:
    """Soft delete a stop."""
    stop_service.delete_stop(current_user, stop_id, get_client_ip(request))
    return success_response({"message": "Stop deleted successfully."})
