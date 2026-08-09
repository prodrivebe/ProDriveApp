"""Vehicle photo API routes."""

import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from sqlalchemy.orm import Session

from app.common.enums import PhotoType
from app.common.responses import SuccessResponse, success_response
from app.config.settings import Settings, get_settings
from app.database.session import get_db
from app.users.models import User
from app.vehicle_photos.permissions import require_photo_actor, require_photo_manager
from app.vehicle_photos.schemas import VehiclePhotoResponse
from app.vehicle_photos.service import VehiclePhotoService

router = APIRouter(prefix="/orders", tags=["Vehicle Photos"])
photo_router = APIRouter(prefix="/photos", tags=["Vehicle Photos"])


def get_client_ip(request: Request) -> str | None:
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip()
    if request.client is not None:
        return request.client.host
    return None


def get_photo_service(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> VehiclePhotoService:
    return VehiclePhotoService(db, settings)


@router.get(
    "/{order_id}/vehicles/{vehicle_id}/photos",
    response_model=SuccessResponse[list[VehiclePhotoResponse]],
)
def list_vehicle_photos(
    order_id: uuid.UUID,
    vehicle_id: uuid.UUID,
    current_user: User = Depends(require_photo_actor),
    photo_service: VehiclePhotoService = Depends(get_photo_service),
) -> SuccessResponse[list[VehiclePhotoResponse]]:
    photos = photo_service.list_photos(current_user, order_id, vehicle_id)
    return success_response([VehiclePhotoResponse.model_validate(photo) for photo in photos])


@router.post(
    "/{order_id}/vehicles/{vehicle_id}/photos",
    response_model=SuccessResponse[VehiclePhotoResponse],
    status_code=201,
)
def upload_vehicle_photo(
    order_id: uuid.UUID,
    vehicle_id: uuid.UUID,
    request: Request,
    file: UploadFile = File(...),
    photo_type: PhotoType = Form(default=PhotoType.FRONT),
    gps_latitude: Decimal | None = Form(default=None),
    gps_longitude: Decimal | None = Form(default=None),
    current_user: User = Depends(require_photo_actor),
    photo_service: VehiclePhotoService = Depends(get_photo_service),
) -> SuccessResponse[VehiclePhotoResponse]:
    photo = photo_service.upload_photo(
        current_user,
        order_id,
        vehicle_id,
        file,
        photo_type=photo_type,
        gps_latitude=gps_latitude,
        gps_longitude=gps_longitude,
        ip_address=get_client_ip(request),
    )
    return success_response(VehiclePhotoResponse.model_validate(photo))


@photo_router.delete("/{photo_id}", response_model=SuccessResponse[dict[str, str]])
def delete_vehicle_photo(
    photo_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(require_photo_manager),
    photo_service: VehiclePhotoService = Depends(get_photo_service),
) -> SuccessResponse[dict[str, str]]:
    photo_service.delete_photo(current_user, photo_id, get_client_ip(request))
    return success_response({"message": "Photo deleted successfully."})
