"""VIN verification API routes."""

import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.common.responses import SuccessResponse, success_response
from app.database.session import get_db
from app.users.models import User
from app.vin_verification.permissions import require_vin_actor
from app.vin_verification.schemas import (
    VinHistoryResponse,
    VinUpdateRequest,
    VinVerificationResponse,
    VinVerifyRequest,
)
from app.vin_verification.service import VinVerificationService

router = APIRouter(prefix="/orders", tags=["VIN Verification"])


def get_client_ip(request: Request) -> str | None:
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip()
    if request.client is not None:
        return request.client.host
    return None


def get_vin_service(db: Session = Depends(get_db)) -> VinVerificationService:
    return VinVerificationService(db)


@router.post(
    "/{order_id}/vehicles/{vehicle_id}/verify-vin",
    response_model=SuccessResponse[VinVerificationResponse],
)
def verify_vin(
    order_id: uuid.UUID,
    vehicle_id: uuid.UUID,
    payload: VinVerifyRequest,
    request: Request,
    current_user: User = Depends(require_vin_actor),
    vin_service: VinVerificationService = Depends(get_vin_service),
) -> SuccessResponse[VinVerificationResponse]:
    """Verify a vehicle VIN."""
    result = vin_service.verify_vin(
        current_user,
        order_id,
        vehicle_id,
        payload.vin,
        get_client_ip(request),
    )
    return success_response(result)


@router.put(
    "/{order_id}/vehicles/{vehicle_id}/vin",
    response_model=SuccessResponse[VinVerificationResponse],
)
def update_vin(
    order_id: uuid.UUID,
    vehicle_id: uuid.UUID,
    payload: VinUpdateRequest,
    request: Request,
    current_user: User = Depends(require_vin_actor),
    vin_service: VinVerificationService = Depends(get_vin_service),
) -> SuccessResponse[VinVerificationResponse]:
    """Update a verified vehicle VIN."""
    result = vin_service.update_vin(
        current_user,
        order_id,
        vehicle_id,
        payload.vin,
        get_client_ip(request),
    )
    return success_response(result)


@router.get(
    "/{order_id}/vehicles/{vehicle_id}/vin-history",
    response_model=SuccessResponse[list[VinHistoryResponse]],
)
def list_vin_history(
    order_id: uuid.UUID,
    vehicle_id: uuid.UUID,
    current_user: User = Depends(require_vin_actor),
    vin_service: VinVerificationService = Depends(get_vin_service),
) -> SuccessResponse[list[VinHistoryResponse]]:
    """Return immutable VIN verification history."""
    history = vin_service.list_history(current_user, order_id, vehicle_id)
    return success_response([VinHistoryResponse.model_validate(entry) for entry in history])
