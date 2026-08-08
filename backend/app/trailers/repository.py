"""Trailer persistence layer."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.trailers.models import Trailer
from app.trailers.schemas import TrailerCreateRequest, TrailerUpdateRequest


class TrailerRepository:
    """Repository for trailer records."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_id_for_company(
        self,
        trailer_id: uuid.UUID,
        company_id: uuid.UUID,
    ) -> Trailer | None:
        """Return a trailer scoped to a company."""
        statement = select(Trailer).where(
            Trailer.id == trailer_id,
            Trailer.company_id == company_id,
            Trailer.deleted_at.is_(None),
        )
        return self._db.scalar(statement)

    def get_by_registration_for_company(
        self,
        registration_number: str,
        company_id: uuid.UUID,
    ) -> Trailer | None:
        """Return a trailer by registration number within a company."""
        statement = select(Trailer).where(
            Trailer.registration_number == registration_number.upper(),
            Trailer.company_id == company_id,
            Trailer.deleted_at.is_(None),
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
    ) -> tuple[list[Trailer], int]:
        """Return paginated trailers for a company."""
        filters = [Trailer.company_id == company_id, Trailer.deleted_at.is_(None)]
        if active is not None:
            filters.append(Trailer.active.is_(active))
        if search:
            pattern = f"%{search.strip()}%"
            filters.append(
                (Trailer.registration_number.ilike(pattern))
                | (Trailer.manufacturer.ilike(pattern))
                | (Trailer.model.ilike(pattern))
                | (Trailer.trailer_type.ilike(pattern))
            )

        total = int(
            self._db.scalar(select(func.count()).select_from(Trailer).where(*filters)) or 0
        )
        statement = (
            select(Trailer)
            .where(*filters)
            .order_by(Trailer.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(self._db.scalars(statement).all()), total

    def count_for_company(self, company_id: uuid.UUID) -> tuple[int, int]:
        """Return total and active trailer counts."""
        base_filters = [Trailer.company_id == company_id, Trailer.deleted_at.is_(None)]
        total = int(
            self._db.scalar(
                select(func.count()).select_from(Trailer).where(*base_filters)
            )
            or 0
        )
        active = int(
            self._db.scalar(
                select(func.count())
                .select_from(Trailer)
                .where(*base_filters, Trailer.active.is_(True))
            )
            or 0
        )
        return total, active

    def create(
        self,
        *,
        company_id: uuid.UUID,
        payload: TrailerCreateRequest,
        created_by: uuid.UUID,
    ) -> Trailer:
        """Create a trailer record."""
        trailer = Trailer(
            company_id=company_id,
            registration_number=payload.registration_number.upper(),
            manufacturer=payload.manufacturer,
            model=payload.model,
            trailer_type=payload.trailer_type,
            maximum_height=(
                float(payload.maximum_height)
                if payload.maximum_height is not None
                else None
            ),
            maximum_weight=(
                float(payload.maximum_weight)
                if payload.maximum_weight is not None
                else None
            ),
            maximum_vehicle_count=payload.maximum_vehicle_count,
            active=payload.active,
            created_by=created_by,
            updated_by=created_by,
        )
        self._db.add(trailer)
        self._db.commit()
        self._db.refresh(trailer)
        return trailer

    def update(
        self,
        trailer: Trailer,
        payload: TrailerUpdateRequest,
        updated_by: uuid.UUID,
    ) -> Trailer:
        """Update a trailer record."""
        trailer.registration_number = payload.registration_number.upper()
        trailer.manufacturer = payload.manufacturer
        trailer.model = payload.model
        trailer.trailer_type = payload.trailer_type
        trailer.maximum_height = float(payload.maximum_height) if payload.maximum_height is not None else None
        trailer.maximum_weight = float(payload.maximum_weight) if payload.maximum_weight is not None else None
        trailer.maximum_vehicle_count = payload.maximum_vehicle_count
        trailer.active = payload.active
        trailer.updated_by = updated_by
        self._db.add(trailer)
        self._db.commit()
        self._db.refresh(trailer)
        return trailer

    def soft_delete(self, trailer: Trailer, deleted_by: uuid.UUID) -> Trailer:
        """Soft delete a trailer record."""
        trailer.deleted_at = datetime.now(tz=UTC)
        trailer.active = False
        trailer.updated_by = deleted_by
        self._db.add(trailer)
        self._db.commit()
        self._db.refresh(trailer)
        return trailer

