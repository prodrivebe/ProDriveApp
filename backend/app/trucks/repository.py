"""Truck persistence layer."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.trucks.models import Truck
from app.trucks.schemas import TruckCreateRequest, TruckUpdateRequest


class TruckRepository:
    """Repository for truck records."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_id_for_company(
        self,
        truck_id: uuid.UUID,
        company_id: uuid.UUID,
    ) -> Truck | None:
        """Return a truck scoped to a company."""
        statement = select(Truck).where(
            Truck.id == truck_id,
            Truck.company_id == company_id,
            Truck.deleted_at.is_(None),
        )
        return self._db.scalar(statement)

    def get_by_registration_for_company(
        self,
        registration_number: str,
        company_id: uuid.UUID,
    ) -> Truck | None:
        """Return a truck by registration number within a company."""
        statement = select(Truck).where(
            Truck.registration_number == registration_number.upper(),
            Truck.company_id == company_id,
            Truck.deleted_at.is_(None),
        )
        return self._db.scalar(statement)

    def list_for_company(
        self,
        company_id: uuid.UUID,
        *,
        page: int,
        page_size: int,
        active: bool | None = None,
        search: str | None = None,
    ) -> tuple[list[Truck], int]:
        """Return paginated trucks for a company."""
        filters = [Truck.company_id == company_id, Truck.deleted_at.is_(None)]
        if active is not None:
            filters.append(Truck.active.is_(active))
        if search:
            pattern = f"%{search.strip()}%"
            filters.append(
                (Truck.registration_number.ilike(pattern))
                | (Truck.brand.ilike(pattern))
                | (Truck.model.ilike(pattern))
                | (Truck.vin.ilike(pattern))
            )

        total = int(
            self._db.scalar(select(func.count()).select_from(Truck).where(*filters)) or 0
        )
        statement = (
            select(Truck)
            .where(*filters)
            .order_by(Truck.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(self._db.scalars(statement).all()), total

    def count_for_company(self, company_id: uuid.UUID) -> tuple[int, int]:
        """Return total and active truck counts."""
        base_filters = [Truck.company_id == company_id, Truck.deleted_at.is_(None)]
        total = int(
            self._db.scalar(select(func.count()).select_from(Truck).where(*base_filters))
            or 0
        )
        active = int(
            self._db.scalar(
                select(func.count())
                .select_from(Truck)
                .where(*base_filters, Truck.active.is_(True))
            )
            or 0
        )
        return total, active

    def create(
        self,
        *,
        company_id: uuid.UUID,
        payload: TruckCreateRequest,
        created_by: uuid.UUID,
    ) -> Truck:
        """Create a truck record."""
        truck = Truck(
            company_id=company_id,
            registration_number=payload.registration_number.upper(),
            brand=payload.brand,
            model=payload.model,
            vin=payload.vin,
            capacity=payload.capacity,
            active=payload.active,
            created_by=created_by,
            updated_by=created_by,
        )
        self._db.add(truck)
        self._db.commit()
        self._db.refresh(truck)
        return truck

    def update(
        self,
        truck: Truck,
        payload: TruckUpdateRequest,
        updated_by: uuid.UUID,
    ) -> Truck:
        """Update a truck record."""
        truck.registration_number = payload.registration_number.upper()
        truck.brand = payload.brand
        truck.model = payload.model
        truck.vin = payload.vin
        truck.capacity = payload.capacity
        truck.active = payload.active
        truck.updated_by = updated_by
        self._db.add(truck)
        self._db.commit()
        self._db.refresh(truck)
        return truck

    def soft_delete(self, truck: Truck, deleted_by: uuid.UUID) -> Truck:
        """Soft delete a truck record."""
        truck.deleted_at = datetime.now(tz=UTC)
        truck.active = False
        truck.updated_by = deleted_by
        self._db.add(truck)
        self._db.commit()
        self._db.refresh(truck)
        return truck
