"""Driver API routes."""

import uuid

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.common.pagination import build_list_meta
from app.common.responses import SuccessResponse, success_response
from app.database.session import get_db
from app.drivers.permissions import require_driver
from app.drivers.schemas import (
    DriverCreateRequest,
    DriverHomeResponse,
    DriverResponse,
    DriverUpdateRequest,
)
from app.drivers.service import DriverService
from app.fleet.permissions import require_fleet_manager
from app.orders.schemas import OrderSummaryResponse
from app.users.models import User
from app.workflow.schemas import DriverCurrentOrderResponse

router = APIRouter(prefix="/drivers", tags=["Drivers"])


def get_client_ip(request: Request) -> str | None:
    """Extract the client IP address from the request."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip()
    if request.client is not None:
        return request.client.host
    return None


def get_driver_service(db: Session = Depends(get_db)) -> DriverService:
    """Provide a driver service instance."""
    return DriverService(db)


@router.get("", response_model=SuccessResponse[list[DriverResponse]])
def list_drivers(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    active: bool | None = Query(default=None),
    search: str | None = Query(default=None),
    current_user: User = Depends(require_fleet_manager),
    driver_service: DriverService = Depends(get_driver_service),
) -> SuccessResponse[list[DriverResponse]]:
    """List drivers for the current company."""
    drivers, total = driver_service.list_drivers(
        current_user,
        page=page,
        page_size=page_size,
        active=active,
        search=search,
    )
    data = [DriverResponse.model_validate(driver) for driver in drivers]
    return success_response(data, meta=build_list_meta(page, page_size, total))


@router.post("", response_model=SuccessResponse[DriverResponse], status_code=201)
def create_driver(
    payload: DriverCreateRequest,
    request: Request,
    current_user: User = Depends(require_fleet_manager),
    driver_service: DriverService = Depends(get_driver_service),
) -> SuccessResponse[DriverResponse]:
    """Create a driver profile."""
    driver = driver_service.create_driver(current_user, payload, get_client_ip(request))
    return success_response(DriverResponse.model_validate(driver))


@router.get("/me", response_model=SuccessResponse[DriverResponse])
def get_my_driver(
    current_user: User = Depends(require_driver),
    driver_service: DriverService = Depends(get_driver_service),
) -> SuccessResponse[DriverResponse]:
    """Return the current driver's profile."""
    driver = driver_service.get_my_driver(current_user)
    return success_response(DriverResponse.model_validate(driver))


@router.get("/me/orders", response_model=SuccessResponse[list[OrderSummaryResponse]])
def list_my_orders(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    current_user: User = Depends(require_driver),
    driver_service: DriverService = Depends(get_driver_service),
) -> SuccessResponse[list[OrderSummaryResponse]]:
    """List orders assigned to the current driver."""
    orders, total = driver_service.list_my_orders(
        current_user,
        page=page,
        page_size=page_size,
    )
    return success_response(orders, meta=build_list_meta(page, page_size, total))


@router.get("/me/current-order", response_model=SuccessResponse[DriverCurrentOrderResponse])
def get_current_order(
    current_user: User = Depends(require_driver),
    driver_service: DriverService = Depends(get_driver_service),
) -> SuccessResponse[DriverCurrentOrderResponse]:
    """Return the driver's active order execution context."""
    return success_response(driver_service.get_current_order(current_user))


@router.get("/me/home", response_model=SuccessResponse[DriverHomeResponse])
def get_driver_home(
    current_user: User = Depends(require_driver),
    driver_service: DriverService = Depends(get_driver_service),
) -> SuccessResponse[DriverHomeResponse]:
    """Return the driver home screen payload."""
    return success_response(driver_service.get_home(current_user))


@router.get("/{driver_id}", response_model=SuccessResponse[DriverResponse])
def get_driver(
    driver_id: uuid.UUID,
    current_user: User = Depends(require_fleet_manager),
    driver_service: DriverService = Depends(get_driver_service),
) -> SuccessResponse[DriverResponse]:
    """Return a driver profile."""
    driver = driver_service.get_driver(current_user, driver_id)
    return success_response(DriverResponse.model_validate(driver))


@router.put("/{driver_id}", response_model=SuccessResponse[DriverResponse])
def update_driver(
    driver_id: uuid.UUID,
    payload: DriverUpdateRequest,
    request: Request,
    current_user: User = Depends(require_fleet_manager),
    driver_service: DriverService = Depends(get_driver_service),
) -> SuccessResponse[DriverResponse]:
    """Update a driver profile."""
    driver = driver_service.update_driver(
        current_user,
        driver_id,
        payload,
        get_client_ip(request),
    )
    return success_response(DriverResponse.model_validate(driver))


@router.delete("/{driver_id}", response_model=SuccessResponse[dict[str, str]])
def delete_driver(
    driver_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(require_fleet_manager),
    driver_service: DriverService = Depends(get_driver_service),
) -> SuccessResponse[dict[str, str]]:
    """Soft delete a driver profile."""
    driver_service.delete_driver(current_user, driver_id, get_client_ip(request))
    return success_response({"message": "Driver deleted successfully."})


@router.get("/{driver_id}/orders", response_model=SuccessResponse[list[OrderSummaryResponse]])
def list_driver_orders(
    driver_id: uuid.UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    current_user: User = Depends(require_fleet_manager),
    driver_service: DriverService = Depends(get_driver_service),
) -> SuccessResponse[list[OrderSummaryResponse]]:
    """List orders assigned to a driver."""
    orders, total = driver_service.list_driver_orders(current_user, driver_id)
    return success_response(orders, meta=build_list_meta(page, page_size, total))
