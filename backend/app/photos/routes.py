"""Vehicle photo API routes."""

import uuid
from decimal import Decimal

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.common.enums import PhotoType
from app.common.responses import SuccessResponse, success_response
from app.config.settings import Settings, get_settings
from app.database.session import get_db
from app.orders.permissions import require_order_actor, require_order_manager
from app.photos.schemas import VehiclePhotoResponse
from app.photos.service import VehiclePhotoService
from app.users.models import User

vehicle_photos_router = APIRouter(tags=["Photos"])
photo_router = APIRouter(prefix="/photos", tags=["Photos"])


def get_photo_service(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> VehiclePhotoService:
    """Provide a vehicle photo service instance."""
    return VehiclePhotoService(db, settings)


@vehicle_photos_router.get(
    "/vehicles/{vehicle_id}/photos",
    response_model=SuccessResponse[list[VehiclePhotoResponse]],
)
def list_vehicle_photos(
    vehicle_id: uuid.UUID,
    current_user: User = Depends(require_order_actor),
    photo_service: VehiclePhotoService = Depends(get_photo_service),
) -> SuccessResponse[list[VehiclePhotoResponse]]:
    """List photos for a vehicle."""
    photos = photo_service.list_photos(current_user, vehicle_id)
    return success_response([VehiclePhotoResponse.model_validate(photo) for photo in photos])


@vehicle_photos_router.post(
    "/vehicles/{vehicle_id}/photos",
    response_model=SuccessResponse[VehiclePhotoResponse],
    status_code=201,
)
def upload_vehicle_photo(
    vehicle_id: uuid.UUID,
    file: UploadFile = File(...),
    photo_type: PhotoType = Form(default=PhotoType.CUSTOM),
    gps_latitude: Decimal | None = Form(default=None),
    gps_longitude: Decimal | None = Form(default=None),
    current_user: User = Depends(require_order_actor),
    photo_service: VehiclePhotoService = Depends(get_photo_service),
) -> SuccessResponse[VehiclePhotoResponse]:
    """Upload a photo for a vehicle."""
    photo = photo_service.upload_photo(
        current_user,
        vehicle_id,
        file,
        photo_type=photo_type,
        gps_latitude=gps_latitude,
        gps_longitude=gps_longitude,
    )
    return success_response(VehiclePhotoResponse.model_validate(photo))


@photo_router.delete("/{photo_id}", response_model=SuccessResponse[dict[str, str]])
def delete_vehicle_photo(
    photo_id: uuid.UUID,
    current_user: User = Depends(require_order_manager),
    photo_service: VehiclePhotoService = Depends(get_photo_service),
) -> SuccessResponse[dict[str, str]]:
    """Delete a vehicle photo."""
    photo_service.delete_photo(current_user, photo_id)
    return success_response({"message": "Photo deleted successfully."})
