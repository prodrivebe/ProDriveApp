"""Order timeline business logic."""

import uuid

from sqlalchemy.orm import Session

from app.orders.models import OrderTimelineEntry
from app.order_timeline.repository import OrderTimelineRepository
from app.realtime.publisher import publish_timeline_entry
from app.users.models import User


class OrderTimelineService:
    """Read-only timeline access and internal event recording."""

    def __init__(self, db: Session) -> None:
        self._repository = OrderTimelineRepository(db)

    def list_for_order(
        self,
        current_user: User,
        order_id: uuid.UUID,
    ) -> list[OrderTimelineEntry]:
        """Return timeline entries for an order."""
        return self._repository.list_for_order(order_id, current_user.company_id)

    def record(
        self,
        current_user: User,
        order_id: uuid.UUID,
        event_type: str,
        description: str,
    ) -> OrderTimelineEntry:
        """Record a timeline event."""
        entry = self._repository.create(
            company_id=current_user.company_id,
            order_id=order_id,
            event_type=event_type,
            description=description,
            created_by=current_user.id,
        )
        publish_timeline_entry(
            company_id=current_user.company_id,
            order_id=order_id,
            entry_id=entry.id,
            event_type=event_type,
            description=description,
            created_at=entry.created_at.isoformat(),
        )
        return entry
