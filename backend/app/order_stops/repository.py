"""Order stop persistence layer."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.enums import StopProgressStatus, StopType
from app.orders.models import OrderStop
from app.order_stops.schemas import OrderStopCreateRequest, OrderStopUpdateRequest


class OrderStopRepository:
    """Repository for order stop records."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_id_for_company(
        self,
        stop_id: uuid.UUID,
        company_id: uuid.UUID,
    ) -> OrderStop | None:
        """Return a stop scoped to a company."""
        statement = select(OrderStop).where(
            OrderStop.id == stop_id,
            OrderStop.company_id == company_id,
            OrderStop.deleted_at.is_(None),
        )
        return self._db.scalar(statement)

    def list_for_order(self, order_id: uuid.UUID, company_id: uuid.UUID) -> list[OrderStop]:
        """Return stops for an order."""
        statement = (
            select(OrderStop)
            .where(
                OrderStop.order_id == order_id,
                OrderStop.company_id == company_id,
                OrderStop.deleted_at.is_(None),
            )
            .order_by(OrderStop.sequence.asc())
        )
        stops = list(self._db.scalars(statement).all())
        stops.sort(
            key=lambda stop: (
                stop.sequence,
                0 if stop.stop_type == StopType.PICKUP else 1,
            )
        )
        return stops

    def create(
        self,
        *,
        company_id: uuid.UUID,
        order_id: uuid.UUID,
        payload: OrderStopCreateRequest,
        created_by: uuid.UUID,
    ) -> OrderStop:
        """Create an order stop."""
        stop = OrderStop(
            company_id=company_id,
            order_id=order_id,
            stop_type=payload.stop_type,
            sequence=payload.sequence,
            company_name=payload.company_name,
            contact_name=payload.contact_name,
            phone=payload.phone,
            address=payload.address,
            city=payload.city,
            postal_code=payload.postal_code,
            country=payload.country,
            latitude=payload.latitude,
            longitude=payload.longitude,
            progress_status=StopProgressStatus.PENDING,
            created_by=created_by,
            updated_by=created_by,
        )
        self._db.add(stop)
        self._db.commit()
        self._db.refresh(stop)
        return stop

    def update(
        self,
        stop: OrderStop,
        payload: OrderStopUpdateRequest,
        updated_by: uuid.UUID,
    ) -> OrderStop:
        """Update an order stop."""
        stop.stop_type = payload.stop_type
        stop.sequence = payload.sequence
        stop.company_name = payload.company_name
        stop.contact_name = payload.contact_name
        stop.phone = payload.phone
        stop.address = payload.address
        stop.city = payload.city
        stop.postal_code = payload.postal_code
        stop.country = payload.country
        stop.latitude = payload.latitude
        stop.longitude = payload.longitude
        stop.updated_by = updated_by
        self._db.add(stop)
        self._db.commit()
        self._db.refresh(stop)
        return stop

    def update_progress(
        self,
        stop: OrderStop,
        progress_status: StopProgressStatus,
        updated_by: uuid.UUID,
    ) -> OrderStop:
        """Update stop progress and arrival/departure timestamps."""
        now = datetime.now(tz=UTC)
        stop.progress_status = progress_status
        stop.updated_by = updated_by
        if progress_status == StopProgressStatus.ARRIVED and stop.arrival_time is None:
            stop.arrival_time = now
        if progress_status == StopProgressStatus.COMPLETED and stop.departure_time is None:
            stop.departure_time = now
        self._db.add(stop)
        self._db.commit()
        self._db.refresh(stop)
        return stop

    def soft_delete(self, stop: OrderStop, deleted_by: uuid.UUID) -> OrderStop:
        """Soft delete an order stop."""
        stop.deleted_at = datetime.now(tz=UTC)
        stop.updated_by = deleted_by
        self._db.add(stop)
        self._db.commit()
        self._db.refresh(stop)
        return stop
