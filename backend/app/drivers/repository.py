"""Driver persistence layer."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.drivers.models import Driver
from app.drivers.schemas import DriverCreateRequest, DriverUpdateRequest


class DriverRepository:
    """Repository for driver records."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_id_for_company(
        self,
        driver_id: uuid.UUID,
        company_id: uuid.UUID,
    ) -> Driver | None:
        """Return a driver scoped to a company."""
        statement = select(Driver).where(
            Driver.id == driver_id,
            Driver.company_id == company_id,
            Driver.deleted_at.is_(None),
        )
        return self._db.scalar(statement)

    def get_by_user_for_company(
        self,
        user_id: uuid.UUID,
        company_id: uuid.UUID,
    ) -> Driver | None:
        """Return a driver profile for a user within a company."""
        statement = select(Driver).where(
            Driver.user_id == user_id,
            Driver.company_id == company_id,
            Driver.deleted_at.is_(None),
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
    ) -> tuple[list[Driver], int]:
        """Return paginated drivers for a company."""
        filters = [Driver.company_id == company_id, Driver.deleted_at.is_(None)]
        if active is not None:
            filters.append(Driver.active.is_(active))
        if search:
            pattern = f"%{search.strip()}%"
            filters.append(
                (Driver.phone.ilike(pattern))
                | (Driver.driving_license.ilike(pattern))
                | (Driver.notes.ilike(pattern))
            )

        total = int(
            self._db.scalar(select(func.count()).select_from(Driver).where(*filters)) or 0
        )
        statement = (
            select(Driver)
            .where(*filters)
            .order_by(Driver.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(self._db.scalars(statement).all()), total

    def count_for_company(self, company_id: uuid.UUID) -> tuple[int, int]:
        """Return total and active driver counts."""
        base_filters = [Driver.company_id == company_id, Driver.deleted_at.is_(None)]
        total = int(
            self._db.scalar(select(func.count()).select_from(Driver).where(*base_filters))
            or 0
        )
        active = int(
            self._db.scalar(
                select(func.count())
                .select_from(Driver)
                .where(*base_filters, Driver.active.is_(True))
            )
            or 0
        )
        return total, active

    def create(
        self,
        *,
        company_id: uuid.UUID,
        payload: DriverCreateRequest,
        created_by: uuid.UUID,
    ) -> Driver:
        """Create a driver profile."""
        driver = Driver(
            company_id=company_id,
            user_id=payload.user_id,
            phone=payload.phone,
            driving_license=payload.driving_license,
            adr_certificate=payload.adr_certificate,
            notes=payload.notes,
            active=payload.active,
            created_by=created_by,
            updated_by=created_by,
        )
        self._db.add(driver)
        self._db.commit()
        self._db.refresh(driver)
        return driver

    def update(
        self,
        driver: Driver,
        payload: DriverUpdateRequest,
        updated_by: uuid.UUID,
    ) -> Driver:
        """Update a driver profile."""
        driver.phone = payload.phone
        driver.driving_license = payload.driving_license
        driver.adr_certificate = payload.adr_certificate
        driver.notes = payload.notes
        driver.active = payload.active
        driver.updated_by = updated_by
        self._db.add(driver)
        self._db.commit()
        self._db.refresh(driver)
        return driver
