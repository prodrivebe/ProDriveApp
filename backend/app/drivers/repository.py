"""Driver persistence layer."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.drivers.models import Driver
from app.drivers.schemas import DriverCreateRequest, DriverUpdateRequest
from app.users.models import User


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
        ).options(selectinload(Driver.user))
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

        search_filter = None
        if search:
            pattern = f"%{search.strip()}%"
            search_filter = (
                (Driver.phone.ilike(pattern))
                | (Driver.driving_license.ilike(pattern))
                | (Driver.notes.ilike(pattern))
                | (User.first_name.ilike(pattern))
                | (User.last_name.ilike(pattern))
            )

        count_statement = select(func.count()).select_from(Driver)
        list_statement = select(Driver)
        if search_filter is not None:
            count_statement = count_statement.join(User, Driver.user_id == User.id).where(
                *filters,
                search_filter,
            )
            list_statement = list_statement.join(User, Driver.user_id == User.id).where(
                *filters,
                search_filter,
            )
        else:
            count_statement = count_statement.where(*filters)
            list_statement = list_statement.where(*filters)

        total = int(self._db.scalar(count_statement) or 0)
        statement = (
            list_statement.order_by(Driver.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(self._db.scalars(statement).all()), total

    def get_by_ids_for_company(
        self,
        driver_ids: set[uuid.UUID],
        company_id: uuid.UUID,
    ) -> dict[uuid.UUID, Driver]:
        """Return drivers keyed by id for batch enrichment."""
        if not driver_ids:
            return {}
        statement = (
            select(Driver)
            .where(
                Driver.id.in_(driver_ids),
                Driver.company_id == company_id,
                Driver.deleted_at.is_(None),
            )
            .options(selectinload(Driver.user))
        )
        drivers = list(self._db.scalars(statement).all())
        return {driver.id: driver for driver in drivers}

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
            address=payload.address,
            country=payload.country,
            date_of_birth=payload.date_of_birth,
            id_document_number=payload.id_document_number,
            id_expiry=payload.id_expiry,
            driving_license=payload.driving_license,
            driving_licence_expiry=payload.driving_licence_expiry,
            adr_certificate=payload.adr_certificate,
            code95_expiry=payload.code95_expiry,
            tachograph_card_number=payload.tachograph_card_number,
            tachograph_card_expiry=payload.tachograph_card_expiry,
            visa_residence_expiry=payload.visa_residence_expiry,
            notes=payload.notes,
            active=payload.active,
            created_by=created_by,
            updated_by=created_by,
        )
        self._db.add(driver)
        self._db.commit()
        self._db.refresh(driver)
        return driver

    def soft_delete(self, driver: Driver, deleted_by: uuid.UUID) -> Driver:
        """Soft delete a driver profile."""
        driver.deleted_at = datetime.now(tz=UTC)
        driver.active = False
        driver.updated_by = deleted_by
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
        driver.address = payload.address
        driver.country = payload.country
        driver.date_of_birth = payload.date_of_birth
        driver.id_document_number = payload.id_document_number
        driver.id_expiry = payload.id_expiry
        driver.driving_license = payload.driving_license
        driver.driving_licence_expiry = payload.driving_licence_expiry
        driver.adr_certificate = payload.adr_certificate
        driver.code95_expiry = payload.code95_expiry
        driver.tachograph_card_number = payload.tachograph_card_number
        driver.tachograph_card_expiry = payload.tachograph_card_expiry
        driver.visa_residence_expiry = payload.visa_residence_expiry
        driver.notes = payload.notes
        driver.active = payload.active
        driver.updated_by = updated_by
        self._db.add(driver)
        self._db.commit()
        self._db.refresh(driver)
        return driver
