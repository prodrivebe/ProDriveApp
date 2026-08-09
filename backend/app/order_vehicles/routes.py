"""Standalone order vehicle API routes."""

import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.common.responses import SuccessResponse, success_response
from app.database.session import get_db
from app.order_vehicles.permissions import require_order_manager
from app.order_vehicles.schemas import OrderVehicleResponse, OrderVehicleUpdateRequest
from app.order_vehicles.service import OrderVehicleService
from app.users.models import User

router = APIRouter(prefix="/vehicles", tags=["Vehicles"])


def get_client_ip(request: Request) -> str | None:
    """Extract the client IP address from the request."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip()
    if request.client is not None:
        return request.client.host
    return None


def get_order_vehicle_service(db: Session = Depends(get_db)) -> OrderVehicleService:
    """Provide an order vehicle service instance."""
    return OrderVehicleService(db)


@router.put("/{vehicle_id}", response_model=SuccessResponse[OrderVehicleResponse])
def update_vehicle(
    vehicle_id: uuid.UUID,
    payload: OrderVehicleUpdateRequest,
    request: Request,
    current_user: User = Depends(require_order_manager),
    vehicle_service: OrderVehicleService = Depends(get_order_vehicle_service),
) -> SuccessResponse[OrderVehicleResponse]:
    """Update a vehicle."""
    vehicle = vehicle_service.update_vehicle(
        current_user,
        vehicle_id,
        payload,
        get_client_ip(request),
    )
    return success_response(OrderVehicleResponse.model_validate(vehicle))


@router.delete("/{vehicle_id}", response_model=SuccessResponse[dict[str, str]])
def delete_vehicle(
    vehicle_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(require_order_manager),
    vehicle_service: OrderVehicleService = Depends(get_order_vehicle_service),
) -> SuccessResponse[dict[str, str]]:
    """Soft delete a vehicle."""
    vehicle_service.delete_vehicle(current_user, vehicle_id, get_client_ip(request))
    return success_response({"message": "Vehicle deleted successfully."})
