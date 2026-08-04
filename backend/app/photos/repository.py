"""Vehicle photo persistence layer."""

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.enums import PhotoType
from app.photos.models import VehiclePhoto


class VehiclePhotoRepository:
    """Repository for vehicle photo records."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_id_for_company(
        self,
        photo_id: uuid.UUID,
        company_id: uuid.UUID,
    ) -> VehiclePhoto | None:
        """Return a photo scoped to a company."""
        statement = select(VehiclePhoto).where(
            VehiclePhoto.id == photo_id,
            VehiclePhoto.company_id == company_id,
        )
        return self._db.scalar(statement)

    def list_for_vehicle(
        self,
        vehicle_id: uuid.UUID,
        company_id: uuid.UUID,
    ) -> list[VehiclePhoto]:
        """Return photos for a vehicle."""
        statement = (
            select(VehiclePhoto)
            .where(
                VehiclePhoto.vehicle_id == vehicle_id,
                VehiclePhoto.company_id == company_id,
            )
            .order_by(VehiclePhoto.uploaded_at.desc())
        )
        return list(self._db.scalars(statement).all())

    def create(
        self,
        *,
        company_id: uuid.UUID,
        vehicle_id: uuid.UUID,
        file_path: str,
        photo_type: PhotoType,
        uploaded_by: uuid.UUID,
        gps_latitude: Decimal | None,
        gps_longitude: Decimal | None,
    ) -> VehiclePhoto:
        """Create a vehicle photo record."""
        photo = VehiclePhoto(
            company_id=company_id,
            vehicle_id=vehicle_id,
            file_path=file_path,
            photo_type=photo_type,
            uploaded_by=uploaded_by,
            uploaded_at=datetime.now(tz=UTC),
            gps_latitude=gps_latitude,
            gps_longitude=gps_longitude,
        )
        self._db.add(photo)
        self._db.commit()
        self._db.refresh(photo)
        return photo

    def delete(self, photo: VehiclePhoto) -> None:
        """Delete a vehicle photo record."""
        self._db.delete(photo)
        self._db.commit()
