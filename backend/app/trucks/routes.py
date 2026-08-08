"""Truck API routes."""

import uuid

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.common.pagination import build_list_meta
from app.common.responses import SuccessResponse, success_response
from app.database.session import get_db
from app.fleet.permissions import require_fleet_manager
from app.trucks.schemas import TruckCreateRequest, TruckResponse, TruckUpdateRequest
from app.trucks.service import TruckService
from app.users.models import User

router = APIRouter(prefix="/trucks", tags=["Trucks"])


def get_client_ip(request: Request) -> str | None:
    """Extract the client IP address from the request."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip()
    if request.client is not None:
        return request.client.host
    return None


def get_truck_service(db: Session = Depends(get_db)) -> TruckService:
    """Provide a truck service instance."""
    return TruckService(db)


@router.get("", response_model=SuccessResponse[list[TruckResponse]])
def list_trucks(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    active: bool | None = Query(default=None),
    search: str | None = Query(default=None),
    current_user: User = Depends(require_fleet_manager),
    truck_service: TruckService = Depends(get_truck_service),
) -> SuccessResponse[list[TruckResponse]]:
    """List trucks for the current company."""
    trucks, total = truck_service.list_trucks(
        current_user,
        page=page,
        page_size=page_size,
        active=active,
        search=search,
    )
    data = [TruckResponse.model_validate(truck) for truck in trucks]
    return success_response(data, meta=build_list_meta(page, page_size, total))


@router.post("", response_model=SuccessResponse[TruckResponse], status_code=201)
def create_truck(
    payload: TruckCreateRequest,
    request: Request,
    current_user: User = Depends(require_fleet_manager),
    truck_service: TruckService = Depends(get_truck_service),
) -> SuccessResponse[TruckResponse]:
    """Create a truck."""
    truck = truck_service.create_truck(current_user, payload, get_client_ip(request))
    return success_response(TruckResponse.model_validate(truck))


@router.get("/{truck_id}", response_model=SuccessResponse[TruckResponse])
def get_truck(
    truck_id: uuid.UUID,
    current_user: User = Depends(require_fleet_manager),
    truck_service: TruckService = Depends(get_truck_service),
) -> SuccessResponse[TruckResponse]:
    """Return a truck."""
    truck = truck_service.get_truck(current_user, truck_id)
    return success_response(TruckResponse.model_validate(truck))


@router.put("/{truck_id}", response_model=SuccessResponse[TruckResponse])
def update_truck(
    truck_id: uuid.UUID,
    payload: TruckUpdateRequest,
    request: Request,
    current_user: User = Depends(require_fleet_manager),
    truck_service: TruckService = Depends(get_truck_service),
) -> SuccessResponse[TruckResponse]:
    """Update a truck."""
    truck = truck_service.update_truck(
        current_user,
        truck_id,
        payload,
        get_client_ip(request),
    )
    return success_response(TruckResponse.model_validate(truck))


@router.delete("/{truck_id}", response_model=SuccessResponse[dict[str, str]])
def delete_truck(
    truck_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(require_fleet_manager),
    truck_service: TruckService = Depends(get_truck_service),
) -> SuccessResponse[dict[str, str]]:
    """Soft delete a truck."""
    truck_service.delete_truck(current_user, truck_id, get_client_ip(request))
    return success_response({"message": "Truck deleted successfully."})
