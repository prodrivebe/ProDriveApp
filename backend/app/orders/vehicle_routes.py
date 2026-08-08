"""Standalone vehicle API routes."""

import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.common.responses import SuccessResponse, success_response
from app.database.session import get_db
from app.orders.permissions import require_order_manager
from app.orders.schemas import (
    OrderVehicleResponse,
    OrderVehicleUpdateRequest,
    VinUpdateRequest,
)
from app.orders.service import OrderService
from app.users.models import User

router = APIRouter(prefix="/vehicles", tags=["Vehicles"])


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


@router.put("/{vehicle_id}", response_model=SuccessResponse[OrderVehicleResponse])
def update_vehicle(
    vehicle_id: uuid.UUID,
    payload: OrderVehicleUpdateRequest,
    current_user: User = Depends(require_order_manager),
    order_service: OrderService = Depends(get_order_service),
) -> SuccessResponse[OrderVehicleResponse]:
    """Update a vehicle."""
    vehicle = order_service.update_vehicle(current_user, vehicle_id, payload)
    return success_response(OrderVehicleResponse.model_validate(vehicle))


@router.delete("/{vehicle_id}", response_model=SuccessResponse[dict[str, str]])
def delete_vehicle(
    vehicle_id: uuid.UUID,
    current_user: User = Depends(require_order_manager),
    order_service: OrderService = Depends(get_order_service),
) -> SuccessResponse[dict[str, str]]:
    """Soft delete a vehicle."""
    order_service.delete_vehicle(current_user, vehicle_id)
    return success_response({"message": "Vehicle deleted successfully."})


@router.post("/{vehicle_id}/scan-vin", response_model=SuccessResponse[OrderVehicleResponse])
def scan_vin(
    vehicle_id: uuid.UUID,
    payload: VinUpdateRequest,
    request: Request,
    current_user: User = Depends(require_order_manager),
    order_service: OrderService = Depends(get_order_service),
) -> SuccessResponse[OrderVehicleResponse]:
    """Scan and store a vehicle VIN."""
    vehicle = order_service.scan_vin(
        current_user,
        vehicle_id,
        payload,
        get_client_ip(request),
    )
    return success_response(OrderVehicleResponse.model_validate(vehicle))


@router.post("/{vehicle_id}/update-vin", response_model=SuccessResponse[OrderVehicleResponse])
def update_vin(
    vehicle_id: uuid.UUID,
    payload: VinUpdateRequest,
    request: Request,
    current_user: User = Depends(require_order_manager),
    order_service: OrderService = Depends(get_order_service),
) -> SuccessResponse[OrderVehicleResponse]:
    """Manually update a vehicle VIN."""
    vehicle = order_service.update_vin(
        current_user,
        vehicle_id,
        payload,
        get_client_ip(request),
    )
    return success_response(OrderVehicleResponse.model_validate(vehicle))
