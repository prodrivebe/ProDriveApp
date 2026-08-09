"""Vehicle damage API routes."""

import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.common.responses import SuccessResponse, success_response
from app.database.session import get_db
from app.users.models import User
from app.vehicle_damage.permissions import require_damage_actor, require_damage_manager
from app.vehicle_damage.schemas import (
    VehicleDamageCreateRequest,
    VehicleDamageResponse,
    VehicleDamageUpdateRequest,
)
from app.vehicle_damage.service import VehicleDamageService

router = APIRouter(prefix="/orders", tags=["Vehicle Damage"])
damage_router = APIRouter(prefix="/damage", tags=["Vehicle Damage"])


def get_client_ip(request: Request) -> str | None:
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip()
    if request.client is not None:
        return request.client.host
    return None


def get_damage_service(db: Session = Depends(get_db)) -> VehicleDamageService:
    return VehicleDamageService(db)


@router.post(
    "/{order_id}/vehicles/{vehicle_id}/damage",
    response_model=SuccessResponse[VehicleDamageResponse],
    status_code=201,
)
def create_damage(
    order_id: uuid.UUID,
    vehicle_id: uuid.UUID,
    payload: VehicleDamageCreateRequest,
    request: Request,
    current_user: User = Depends(require_damage_actor),
    damage_service: VehicleDamageService = Depends(get_damage_service),
) -> SuccessResponse[VehicleDamageResponse]:
    damage = damage_service.create_damage(
        current_user,
        order_id,
        vehicle_id,
        payload,
        get_client_ip(request),
    )
    return success_response(damage)


@router.get(
    "/{order_id}/vehicles/{vehicle_id}/damage",
    response_model=SuccessResponse[list[VehicleDamageResponse]],
)
def list_damage(
    order_id: uuid.UUID,
    vehicle_id: uuid.UUID,
    current_user: User = Depends(require_damage_actor),
    damage_service: VehicleDamageService = Depends(get_damage_service),
) -> SuccessResponse[list[VehicleDamageResponse]]:
    damage = damage_service.list_damage(current_user, order_id, vehicle_id)
    return success_response(damage)


@damage_router.put("/{damage_id}", response_model=SuccessResponse[VehicleDamageResponse])
def update_damage(
    damage_id: uuid.UUID,
    payload: VehicleDamageUpdateRequest,
    request: Request,
    current_user: User = Depends(require_damage_manager),
    damage_service: VehicleDamageService = Depends(get_damage_service),
) -> SuccessResponse[VehicleDamageResponse]:
    damage = damage_service.update_damage(
        current_user,
        damage_id,
        payload,
        get_client_ip(request),
    )
    return success_response(damage)


@damage_router.delete("/{damage_id}", response_model=SuccessResponse[dict[str, str]])
def delete_damage(
    damage_id: uuid.UUID,
    current_user: User = Depends(require_damage_manager),
    damage_service: VehicleDamageService = Depends(get_damage_service),
) -> SuccessResponse[dict[str, str]]:
    damage_service.delete_damage(current_user, damage_id)
    return success_response({"message": "Damage report deleted successfully."})
