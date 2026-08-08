"""Trailer API routes."""

import uuid

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.common.pagination import build_list_meta
from app.common.responses import SuccessResponse, success_response
from app.database.session import get_db
from app.fleet.permissions import require_fleet_manager
from app.trailers.schemas import (
    TrailerCreateRequest,
    TrailerResponse,
    TrailerUpdateRequest,
)
from app.trailers.service import TrailerService
from app.users.models import User

router = APIRouter(prefix="/trailers", tags=["Trailers"])


def get_client_ip(request: Request) -> str | None:
    """Extract the client IP address from the request."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip()
    if request.client is not None:
        return request.client.host
    return None


def get_trailer_service(db: Session = Depends(get_db)) -> TrailerService:
    """Provide a trailer service instance."""
    return TrailerService(db)


@router.get("", response_model=SuccessResponse[list[TrailerResponse]])
def list_trailers(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    active: bool | None = Query(default=None),
    search: str | None = Query(default=None),
    current_user: User = Depends(require_fleet_manager),
    trailer_service: TrailerService = Depends(get_trailer_service),
) -> SuccessResponse[list[TrailerResponse]]:
    """List trailers for the current company."""
    trailers, total = trailer_service.list_trailers(
        current_user,
        page=page,
        page_size=page_size,
        active=active,
        search=search,
    )
    data = [TrailerResponse.model_validate(trailer) for trailer in trailers]
    return success_response(data, meta=build_list_meta(page, page_size, total))


@router.post("", response_model=SuccessResponse[TrailerResponse], status_code=201)
def create_trailer(
    payload: TrailerCreateRequest,
    request: Request,
    current_user: User = Depends(require_fleet_manager),
    trailer_service: TrailerService = Depends(get_trailer_service),
) -> SuccessResponse[TrailerResponse]:
    """Create a trailer."""
    trailer = trailer_service.create_trailer(current_user, payload, get_client_ip(request))
    return success_response(TrailerResponse.model_validate(trailer))


@router.get("/{trailer_id}", response_model=SuccessResponse[TrailerResponse])
def get_trailer(
    trailer_id: uuid.UUID,
    current_user: User = Depends(require_fleet_manager),
    trailer_service: TrailerService = Depends(get_trailer_service),
) -> SuccessResponse[TrailerResponse]:
    """Return a trailer."""
    trailer = trailer_service.get_trailer(current_user, trailer_id)
    return success_response(TrailerResponse.model_validate(trailer))


@router.put("/{trailer_id}", response_model=SuccessResponse[TrailerResponse])
def update_trailer(
    trailer_id: uuid.UUID,
    payload: TrailerUpdateRequest,
    request: Request,
    current_user: User = Depends(require_fleet_manager),
    trailer_service: TrailerService = Depends(get_trailer_service),
) -> SuccessResponse[TrailerResponse]:
    """Update a trailer."""
    trailer = trailer_service.update_trailer(
        current_user,
        trailer_id,
        payload,
        get_client_ip(request),
    )
    return success_response(TrailerResponse.model_validate(trailer))


@router.delete("/{trailer_id}", response_model=SuccessResponse[dict[str, str]])
def delete_trailer(
    trailer_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(require_fleet_manager),
    trailer_service: TrailerService = Depends(get_trailer_service),
) -> SuccessResponse[dict[str, str]]:
    """Soft delete a trailer."""
    trailer_service.delete_trailer(current_user, trailer_id, get_client_ip(request))
    return success_response({"message": "Trailer deleted successfully."})
