"""Order timeline persistence layer."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.orders.models import OrderTimelineEntry


class OrderTimelineRepository:
    """Repository for order timeline records."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def list_for_order(
        self,
        order_id: uuid.UUID,
        company_id: uuid.UUID,
    ) -> list[OrderTimelineEntry]:
        """Return timeline entries for an order."""
        statement = (
            select(OrderTimelineEntry)
            .where(
                OrderTimelineEntry.order_id == order_id,
                OrderTimelineEntry.company_id == company_id,
            )
            .order_by(OrderTimelineEntry.created_at.asc())
        )
        return list(self._db.scalars(statement).all())

    def create(
        self,
        *,
        company_id: uuid.UUID,
        order_id: uuid.UUID,
        event_type: str,
        description: str,
        created_by: uuid.UUID | None,
    ) -> OrderTimelineEntry:
        """Create a timeline entry."""
        entry = OrderTimelineEntry(
            company_id=company_id,
            order_id=order_id,
            event_type=event_type,
            description=description,
            created_by=created_by,
            created_at=datetime.now(tz=UTC),
        )
        self._db.add(entry)
        self._db.commit()
        self._db.refresh(entry)
        return entry
