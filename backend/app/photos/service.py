"""Vehicle photo business logic."""

import uuid
from decimal import Decimal

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.common.enums import PhotoType
from app.common.exceptions import NotFoundError
from app.common.storage.local import LocalFileStorage
from app.config.settings import Settings
from app.orders.models import OrderVehicle
from app.orders.repository import OrderVehicleRepository
from app.orders.service import OrderService
from app.photos.models import VehiclePhoto
from app.photos.repository import VehiclePhotoRepository
from app.users.models import User


class VehiclePhotoService:
    """Vehicle photo upload workflows."""

    def __init__(self, db: Session, settings: Settings) -> None:
        self._db = db
        self._photos = VehiclePhotoRepository(db)
        self._vehicles = OrderVehicleRepository(db)
        self._orders = OrderService(db)
        self._storage = LocalFileStorage(settings)

    def list_photos(self, current_user: User, vehicle_id: uuid.UUID) -> list[VehiclePhoto]:
        """List photos for a vehicle."""
        self._get_vehicle(current_user, vehicle_id)
        return self._photos.list_for_vehicle(vehicle_id, current_user.company_id)

    def upload_photo(
        self,
        current_user: User,
        vehicle_id: uuid.UUID,
        upload_file: UploadFile,
        *,
        photo_type: PhotoType,
        gps_latitude: Decimal | None,
        gps_longitude: Decimal | None,
    ) -> VehiclePhoto:
        """Upload a photo for a vehicle."""
        vehicle = self._get_vehicle(current_user, vehicle_id)
        file_path = self._storage.save_vehicle_photo(
            company_id=current_user.company_id,
            vehicle_id=vehicle_id,
            upload_file=upload_file,
        )
        photo = self._photos.create(
            company_id=current_user.company_id,
            vehicle_id=vehicle_id,
            file_path=file_path,
            photo_type=photo_type,
            uploaded_by=current_user.id,
            gps_latitude=gps_latitude,
            gps_longitude=gps_longitude,
        )
        self._orders.record_timeline_event(
            current_user,
            vehicle.order_id,
            "PHOTOS_UPLOADED",
            f"Vehicle photo uploaded ({photo_type.value}).",
        )
        return photo

    def delete_photo(self, current_user: User, photo_id: uuid.UUID) -> None:
        """Delete a vehicle photo."""
        photo = self._photos.get_by_id_for_company(photo_id, current_user.company_id)
        if photo is None:
            raise NotFoundError(code="PHOTO_NOT_FOUND", message="Photo not found.")
        self._storage.delete_file(photo.file_path)
        self._photos.delete(photo)

    def _get_vehicle(self, current_user: User, vehicle_id: uuid.UUID) -> OrderVehicle:
        vehicle = self._vehicles.get_by_id_for_company(vehicle_id, current_user.company_id)
        if vehicle is None:
            raise NotFoundError(code="VEHICLE_NOT_FOUND", message="Vehicle not found.")
        self._orders.get_order(current_user, vehicle.order_id)
        return vehicle
