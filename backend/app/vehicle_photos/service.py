"""Vehicle photo business logic."""

import json
import uuid
from decimal import Decimal

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.audit.service import AuditService
from app.common.enums import PhotoType
from app.common.execution_access import (
    ensure_execution_access,
    get_order_for_company,
    get_vehicle_for_order,
)
from app.common.exceptions import NotFoundError
from app.common.storage.local import LocalFileStorage
from app.config.settings import Settings
from app.drivers.repository import DriverRepository
from app.order_timeline.service import OrderTimelineService
from app.order_vehicles.repository import OrderVehicleRepository
from app.orders.repository import OrderRepository
from app.users.models import User
from app.realtime.publisher import publish_vehicle_execution_event
from app.realtime.schemas import RealtimeEventType
from app.vehicle_photos.models import VehiclePhoto
from app.vehicle_photos.repository import VehiclePhotoRepository


class VehiclePhotoService:
    """Vehicle photo upload workflows."""

    def __init__(self, db: Session, settings: Settings) -> None:
        self._db = db
        self._photos = VehiclePhotoRepository(db)
        self._vehicles = OrderVehicleRepository(db)
        self._orders = OrderRepository(db)
        self._drivers = DriverRepository(db)
        self._timeline = OrderTimelineService(db)
        self._audit = AuditService(db)
        self._storage = LocalFileStorage(settings)

    def list_photos(
        self,
        current_user: User,
        order_id: uuid.UUID,
        vehicle_id: uuid.UUID,
    ) -> list[VehiclePhoto]:
        order = get_order_for_company(self._orders, order_id, current_user.company_id)
        ensure_execution_access(current_user, order, self._drivers)
        get_vehicle_for_order(
            self._vehicles,
            order_id=order_id,
            vehicle_id=vehicle_id,
            company_id=current_user.company_id,
        )
        return self._photos.list_for_vehicle(vehicle_id, current_user.company_id)

    def upload_photo(
        self,
        current_user: User,
        order_id: uuid.UUID,
        vehicle_id: uuid.UUID,
        upload_file: UploadFile,
        *,
        photo_type: PhotoType,
        gps_latitude: Decimal | None = None,
        gps_longitude: Decimal | None = None,
        metadata: dict[str, str] | None = None,
        ip_address: str | None = None,
    ) -> VehiclePhoto:
        order = get_order_for_company(self._orders, order_id, current_user.company_id)
        ensure_execution_access(current_user, order, self._drivers)
        get_vehicle_for_order(
            self._vehicles,
            order_id=order_id,
            vehicle_id=vehicle_id,
            company_id=current_user.company_id,
        )
        file_path, file_name, file_size, content_type = self._storage.save_vehicle_photo(
            company_id=current_user.company_id,
            order_id=order_id,
            vehicle_id=vehicle_id,
            upload_file=upload_file,
        )
        photo = self._photos.create(
            company_id=current_user.company_id,
            order_id=order_id,
            vehicle_id=vehicle_id,
            file_path=file_path,
            file_name=file_name,
            file_size=file_size,
            content_type=content_type,
            photo_type=photo_type,
            uploaded_by=current_user.id,
            metadata_json=json.dumps(metadata) if metadata else None,
            gps_latitude=gps_latitude,
            gps_longitude=gps_longitude,
        )
        self._timeline.record(
            current_user,
            order_id,
            "PHOTO_UPLOADED",
            f"Vehicle photo uploaded ({photo_type.value}).",
        )
        self._audit.record_vehicle_photo_uploaded(
            company_id=current_user.company_id,
            user_id=current_user.id,
            entity_id=str(photo.id),
            ip_address=ip_address,
        )
        publish_vehicle_execution_event(
            company_id=current_user.company_id,
            order_id=order_id,
            vehicle_id=vehicle_id,
            event_type=RealtimeEventType.PHOTO_UPLOADED,
            order_number=order.order_number,
            extra={"photo_id": str(photo.id), "photo_type": photo_type.value},
            driver_user_id=current_user.id,
        )
        return photo

    def delete_photo(
        self,
        current_user: User,
        photo_id: uuid.UUID,
        ip_address: str | None = None,
    ) -> None:
        photo = self._photos.get_by_id_for_company(photo_id, current_user.company_id)
        if photo is None or photo.order_id is None:
            raise NotFoundError(code="PHOTO_NOT_FOUND", message="Photo not found.")
        order = get_order_for_company(
            self._orders,
            photo.order_id,
            current_user.company_id,
        )
        ensure_execution_access(current_user, order, self._drivers)
        self._storage.delete_file(photo.file_path)
        self._photos.delete(photo)
        self._timeline.record(
            current_user,
            photo.order_id,
            "PHOTO_DELETED",
            "Vehicle photo deleted.",
        )
        self._audit.record_vehicle_photo_deleted(
            company_id=current_user.company_id,
            user_id=current_user.id,
            entity_id=str(photo_id),
            ip_address=ip_address,
        )

    def get_photo_for_company(
        self,
        photo_id: uuid.UUID,
        company_id: uuid.UUID,
    ) -> VehiclePhoto | None:
        return self._photos.get_by_id_for_company(photo_id, company_id)
