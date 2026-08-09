"""Completion checklist persistence layer."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.completion_checklist.models import OrderCompletionChecklist


class CompletionChecklistRepository:
    """Repository for order completion checklist snapshots."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def get_for_order(
        self,
        order_id: uuid.UUID,
        company_id: uuid.UUID,
    ) -> OrderCompletionChecklist | None:
        statement = select(OrderCompletionChecklist).where(
            OrderCompletionChecklist.order_id == order_id,
            OrderCompletionChecklist.company_id == company_id,
        )
        return self._db.scalar(statement)

    def upsert(
        self,
        *,
        company_id: uuid.UUID,
        order_id: uuid.UUID,
        pickup_completed: bool,
        delivery_completed: bool,
        vins_verified: bool,
        photos_uploaded: bool,
        documents_uploaded: bool,
        damage_reports_completed: bool,
        can_complete: bool,
        completion_percentage: int,
    ) -> OrderCompletionChecklist:
        checklist = self.get_for_order(order_id, company_id)
        if checklist is None:
            checklist = OrderCompletionChecklist(
                company_id=company_id,
                order_id=order_id,
            )
        checklist.pickup_completed = pickup_completed
        checklist.delivery_completed = delivery_completed
        checklist.vins_verified = vins_verified
        checklist.photos_uploaded = photos_uploaded
        checklist.documents_uploaded = documents_uploaded
        checklist.damage_reports_completed = damage_reports_completed
        checklist.can_complete = can_complete
        checklist.completion_percentage = completion_percentage
        checklist.updated_at = datetime.now(tz=UTC)
        self._db.add(checklist)
        self._db.commit()
        self._db.refresh(checklist)
        return checklist
