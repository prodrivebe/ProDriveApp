"""Order API routes."""

import uuid

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.common.enums import OrderStatus
from app.common.pagination import build_list_meta
from app.common.responses import SuccessResponse, success_response
from app.database.session import get_db
from app.orders.permissions import require_order_actor, require_order_manager
from app.orders.schemas import (
    AssignDriverRequest,
    OrderCreateRequest,
    OrderListResponse,
    OrderResponse,
    OrderStopCreateRequest,
    OrderStopResponse,
    OrderTimelineResponse,
    OrderUpdateRequest,
    OrderVehicleCreateRequest,
    OrderVehicleResponse,
)
from app.orders.service import OrderService
from app.users.models import User

router = APIRouter(prefix="/orders", tags=["Orders"])


def get_client_ip(request: Request) -> str | None:
    """Extract the client IP address from the request."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    if request.client is not None:
        return request.client.host
    return None


def get_order_service(db: Session = Depends(get_db)) -> OrderService:
    """Provide an order service instance."""
    return OrderService(db)


@router.get("", response_model=SuccessResponse[list[OrderListResponse]])
def list_orders(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    status: OrderStatus | None = Query(default=None),
    customer_id: uuid.UUID | None = Query(default=None),
    driver_id: uuid.UUID | None = Query(default=None),
    search: str | None = Query(default=None),
    current_user: User = Depends(require_order_manager),
    order_service: OrderService = Depends(get_order_service),
) -> SuccessResponse[list[OrderListResponse]]:
    """List orders for the current company."""
    orders, total = order_service.list_orders(
        current_user,
        page=page,
        page_size=page_size,
        status=status,
        customer_id=customer_id,
        driver_id=driver_id,
        search=search,
    )
    data = [OrderListResponse.model_validate(order) for order in orders]
    return success_response(data, meta=build_list_meta(page, page_size, total))


@router.post("", response_model=SuccessResponse[OrderResponse], status_code=201)
def create_order(
    payload: OrderCreateRequest,
    request: Request,
    current_user: User = Depends(require_order_manager),
    order_service: OrderService = Depends(get_order_service),
) -> SuccessResponse[OrderResponse]:
    """Create an order."""
    order = order_service.create_order(current_user, payload, get_client_ip(request))
    return success_response(OrderResponse.model_validate(order))


@router.get("/{order_id}", response_model=SuccessResponse[OrderResponse])
def get_order(
    order_id: uuid.UUID,
    current_user: User = Depends(require_order_actor),
    order_service: OrderService = Depends(get_order_service),
) -> SuccessResponse[OrderResponse]:
    """Return an order."""
    order = order_service.get_order(current_user, order_id)
    return success_response(OrderResponse.model_validate(order))


@router.put("/{order_id}", response_model=SuccessResponse[OrderResponse])
def update_order(
    order_id: uuid.UUID,
    payload: OrderUpdateRequest,
    request: Request,
    current_user: User = Depends(require_order_manager),
    order_service: OrderService = Depends(get_order_service),
) -> SuccessResponse[OrderResponse]:
    """Update an order."""
    order = order_service.update_order(
        current_user,
        order_id,
        payload,
        get_client_ip(request),
    )
    return success_response(OrderResponse.model_validate(order))


@router.delete("/{order_id}", response_model=SuccessResponse[dict[str, str]])
def delete_order(
    order_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(require_order_manager),
    order_service: OrderService = Depends(get_order_service),
) -> SuccessResponse[dict[str, str]]:
    """Soft delete an order."""
    order_service.delete_order(current_user, order_id, get_client_ip(request))
    return success_response({"message": "Order deleted successfully."})


@router.get("/{order_id}/stops", response_model=SuccessResponse[list[OrderStopResponse]])
def list_stops(
    order_id: uuid.UUID,
    current_user: User = Depends(require_order_actor),
    order_service: OrderService = Depends(get_order_service),
) -> SuccessResponse[list[OrderStopResponse]]:
    """List stops for an order."""
    stops = order_service.list_stops(current_user, order_id)
    return success_response([OrderStopResponse.model_validate(stop) for stop in stops])


@router.post(
    "/{order_id}/stops",
    response_model=SuccessResponse[OrderStopResponse],
    status_code=201,
)
def create_stop(
    order_id: uuid.UUID,
    payload: OrderStopCreateRequest,
    current_user: User = Depends(require_order_manager),
    order_service: OrderService = Depends(get_order_service),
) -> SuccessResponse[OrderStopResponse]:
    """Create a stop on an order."""
    stop = order_service.create_stop(current_user, order_id, payload)
    return success_response(OrderStopResponse.model_validate(stop))


@router.get("/{order_id}/vehicles", response_model=SuccessResponse[list[OrderVehicleResponse]])
def list_vehicles(
    order_id: uuid.UUID,
    current_user: User = Depends(require_order_actor),
    order_service: OrderService = Depends(get_order_service),
) -> SuccessResponse[list[OrderVehicleResponse]]:
    """List vehicles for an order."""
    vehicles = order_service.list_vehicles(current_user, order_id)
    return success_response(
        [OrderVehicleResponse.model_validate(vehicle) for vehicle in vehicles]
    )


@router.post(
    "/{order_id}/vehicles",
    response_model=SuccessResponse[OrderVehicleResponse],
    status_code=201,
)
def create_vehicle(
    order_id: uuid.UUID,
    payload: OrderVehicleCreateRequest,
    current_user: User = Depends(require_order_manager),
    order_service: OrderService = Depends(get_order_service),
) -> SuccessResponse[OrderVehicleResponse]:
    """Create a vehicle on an order."""
    vehicle = order_service.create_vehicle(current_user, order_id, payload)
    return success_response(OrderVehicleResponse.model_validate(vehicle))


@router.post("/{order_id}/assign-driver", response_model=SuccessResponse[OrderResponse])
def assign_driver(
    order_id: uuid.UUID,
    payload: AssignDriverRequest,
    request: Request,
    current_user: User = Depends(require_order_manager),
    order_service: OrderService = Depends(get_order_service),
) -> SuccessResponse[OrderResponse]:
    """Assign a driver and optional fleet resources."""
    order = order_service.assign_driver(
        current_user,
        order_id,
        payload,
        get_client_ip(request),
    )
    return success_response(OrderResponse.model_validate(order))


@router.post("/{order_id}/accept", response_model=SuccessResponse[OrderResponse])
def accept_order(
    order_id: uuid.UUID,
    current_user: User = Depends(require_order_actor),
    order_service: OrderService = Depends(get_order_service),
) -> SuccessResponse[OrderResponse]:
    """Accept an assigned order."""
    order = order_service.accept_order(current_user, order_id)
    return success_response(OrderResponse.model_validate(order))


@router.post("/{order_id}/reject", response_model=SuccessResponse[OrderResponse])
def reject_order(
    order_id: uuid.UUID,
    current_user: User = Depends(require_order_actor),
    order_service: OrderService = Depends(get_order_service),
) -> SuccessResponse[OrderResponse]:
    """Reject an assigned order."""
    order = order_service.reject_order(current_user, order_id)
    return success_response(OrderResponse.model_validate(order))


@router.post("/{order_id}/arrive-pickup", response_model=SuccessResponse[OrderResponse])
def arrive_pickup(
    order_id: uuid.UUID,
    current_user: User = Depends(require_order_actor),
    order_service: OrderService = Depends(get_order_service),
) -> SuccessResponse[OrderResponse]:
    """Mark arrival at pickup."""
    order = order_service.arrive_pickup(current_user, order_id)
    return success_response(OrderResponse.model_validate(order))


@router.post("/{order_id}/complete-loading", response_model=SuccessResponse[OrderResponse])
def complete_loading(
    order_id: uuid.UUID,
    current_user: User = Depends(require_order_actor),
    order_service: OrderService = Depends(get_order_service),
) -> SuccessResponse[OrderResponse]:
    """Mark loading complete."""
    order = order_service.complete_loading(current_user, order_id)
    return success_response(OrderResponse.model_validate(order))


@router.post("/{order_id}/arrive-delivery", response_model=SuccessResponse[OrderResponse])
def arrive_delivery(
    order_id: uuid.UUID,
    current_user: User = Depends(require_order_actor),
    order_service: OrderService = Depends(get_order_service),
) -> SuccessResponse[OrderResponse]:
    """Mark arrival at delivery."""
    order = order_service.arrive_delivery(current_user, order_id)
    return success_response(OrderResponse.model_validate(order))


@router.post("/{order_id}/complete-delivery", response_model=SuccessResponse[OrderResponse])
def complete_delivery(
    order_id: uuid.UUID,
    current_user: User = Depends(require_order_actor),
    order_service: OrderService = Depends(get_order_service),
) -> SuccessResponse[OrderResponse]:
    """Mark delivery complete."""
    order = order_service.complete_delivery(current_user, order_id)
    return success_response(OrderResponse.model_validate(order))


@router.post("/{order_id}/cancel", response_model=SuccessResponse[OrderResponse])
def cancel_order(
    order_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(require_order_manager),
    order_service: OrderService = Depends(get_order_service),
) -> SuccessResponse[OrderResponse]:
    """Cancel an order."""
    order = order_service.cancel_order(current_user, order_id, get_client_ip(request))
    return success_response(OrderResponse.model_validate(order))


@router.get("/{order_id}/timeline", response_model=SuccessResponse[list[OrderTimelineResponse]])
def list_timeline(
    order_id: uuid.UUID,
    current_user: User = Depends(require_order_actor),
    order_service: OrderService = Depends(get_order_service),
) -> SuccessResponse[list[OrderTimelineResponse]]:
    """Return order timeline entries."""
    entries = order_service.list_timeline(current_user, order_id)
    return success_response([OrderTimelineResponse.model_validate(entry) for entry in entries])
