"""Vehicle damage persistence layer."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.vehicle_damage.models import VehicleDamage, VehicleDamagePhoto


class VehicleDamageRepository:
    """Repository for vehicle damage records."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_id_for_company(
        self,
        damage_id: uuid.UUID,
        company_id: uuid.UUID,
    ) -> VehicleDamage | None:
        statement = select(VehicleDamage).where(
            VehicleDamage.id == damage_id,
            VehicleDamage.company_id == company_id,
            VehicleDamage.deleted_at.is_(None),
        )
        return self._db.scalar(statement)

    def list_for_vehicle(
        self,
        vehicle_id: uuid.UUID,
        company_id: uuid.UUID,
    ) -> list[VehicleDamage]:
        statement = (
            select(VehicleDamage)
            .where(
                VehicleDamage.vehicle_id == vehicle_id,
                VehicleDamage.company_id == company_id,
                VehicleDamage.deleted_at.is_(None),
            )
            .order_by(VehicleDamage.reported_at.desc())
        )
        return list(self._db.scalars(statement).all())

    def create(
        self,
        *,
        company_id: uuid.UUID,
        order_id: uuid.UUID,
        vehicle_id: uuid.UUID,
        damage_type: str,
        severity: str,
        description: str | None,
        location: str | None,
        reported_by: uuid.UUID,
    ) -> VehicleDamage:
        damage = VehicleDamage(
            company_id=company_id,
            order_id=order_id,
            vehicle_id=vehicle_id,
            damage_type=damage_type,
            severity=severity,
            description=description,
            location=location,
            reported_by=reported_by,
            reported_at=datetime.now(tz=UTC),
        )
        self._db.add(damage)
        self._db.commit()
        self._db.refresh(damage)
        return damage

    def update(
        self,
        damage: VehicleDamage,
        *,
        damage_type: str,
        severity: str,
        description: str | None,
        location: str | None,
    ) -> VehicleDamage:
        damage.damage_type = damage_type
        damage.severity = severity
        damage.description = description
        damage.location = location
        self._db.add(damage)
        self._db.commit()
        self._db.refresh(damage)
        return damage

    def soft_delete(self, damage: VehicleDamage) -> VehicleDamage:
        damage.deleted_at = datetime.now(tz=UTC)
        self._db.add(damage)
        self._db.commit()
        self._db.refresh(damage)
        return damage

    def replace_photos(self, damage_id: uuid.UUID, photo_ids: list[uuid.UUID]) -> None:
        existing = self._db.scalars(
            select(VehicleDamagePhoto).where(VehicleDamagePhoto.damage_id == damage_id)
        ).all()
        for link in existing:
            self._db.delete(link)
        for photo_id in photo_ids:
            self._db.add(VehicleDamagePhoto(damage_id=damage_id, photo_id=photo_id))
        self._db.commit()

    def list_photo_ids(self, damage_id: uuid.UUID) -> list[uuid.UUID]:
        rows = self._db.scalars(
            select(VehicleDamagePhoto.photo_id).where(
                VehicleDamagePhoto.damage_id == damage_id
            )
        ).all()
        return list(rows)
