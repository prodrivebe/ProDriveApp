"""Order stop business logic."""

import uuid

from sqlalchemy.orm import Session

from app.audit.service import AuditService
from app.common.exceptions import NotFoundError
from app.order_stops.repository import OrderStopRepository
from app.order_stops.schemas import OrderStopCreateRequest, OrderStopUpdateRequest
from app.order_stops.validators import validate_stop_sequence_for_order
from app.order_timeline.service import OrderTimelineService
from app.orders.models import OrderStop
from app.orders.repository import OrderRepository
from app.orders.validators import validate_order_editable
from app.users.models import User


class OrderStopService:
    """Order stop management workflows."""

    def __init__(self, db: Session) -> None:
        self._db = db
        self._stops = OrderStopRepository(db)
        self._orders = OrderRepository(db)
        self._timeline = OrderTimelineService(db)
        self._audit = AuditService(db)

    def _get_editable_order(self, current_user: User, order_id: uuid.UUID):
        order = self._orders.get_by_id_for_company(order_id, current_user.company_id)
        if order is None:
            raise NotFoundError(code="ORDER_NOT_FOUND", message="Order not found.")
        validate_order_editable(order)
        return order

    def list_stops(self, current_user: User, order_id: uuid.UUID) -> list[OrderStop]:
        """List stops for an order."""
        order = self._orders.get_by_id_for_company(order_id, current_user.company_id)
        if order is None:
            raise NotFoundError(code="ORDER_NOT_FOUND", message="Order not found.")
        return self._stops.list_for_order(order_id, current_user.company_id)

    def create_stop(
        self,
        current_user: User,
        order_id: uuid.UUID,
        payload: OrderStopCreateRequest,
        ip_address: str | None,
    ) -> OrderStop:
        """Create a stop on an order."""
        self._get_editable_order(current_user, order_id)
        existing_stops = self._stops.list_for_order(order_id, current_user.company_id)
        validate_stop_sequence_for_order(existing_stops, payload.sequence)
        stop = self._stops.create(
            company_id=current_user.company_id,
            order_id=order_id,
            payload=payload,
            created_by=current_user.id,
        )
        self._timeline.record(
            current_user,
            order_id,
            "STOP_ADDED",
            f"{payload.stop_type.value} stop added at sequence {payload.sequence}.",
        )
        self._audit.record_order_stop_added(
            company_id=current_user.company_id,
            user_id=current_user.id,
            entity_id=str(stop.id),
            ip_address=ip_address,
        )
        return stop

    def update_stop(
        self,
        current_user: User,
        stop_id: uuid.UUID,
        payload: OrderStopUpdateRequest,
        ip_address: str | None,
    ) -> OrderStop:
        """Update a stop."""
        stop = self._stops.get_by_id_for_company(stop_id, current_user.company_id)
        if stop is None:
            raise NotFoundError(code="STOP_NOT_FOUND", message="Stop not found.")
        self._get_editable_order(current_user, stop.order_id)
        existing_stops = self._stops.list_for_order(stop.order_id, current_user.company_id)
        validate_stop_sequence_for_order(
            existing_stops,
            payload.sequence,
            exclude_stop_id=stop.id,
        )
        updated_stop = self._stops.update(stop, payload, current_user.id)
        self._timeline.record(
            current_user,
            stop.order_id,
            "ORDER_UPDATED",
            f"Stop sequence {payload.sequence} updated.",
        )
        self._audit.record_order_stop_updated(
            company_id=current_user.company_id,
            user_id=current_user.id,
            entity_id=str(updated_stop.id),
            ip_address=ip_address,
        )
        return updated_stop

    def delete_stop(
        self,
        current_user: User,
        stop_id: uuid.UUID,
        ip_address: str | None,
    ) -> None:
        """Soft delete a stop."""
        stop = self._stops.get_by_id_for_company(stop_id, current_user.company_id)
        if stop is None:
            raise NotFoundError(code="STOP_NOT_FOUND", message="Stop not found.")
        self._get_editable_order(current_user, stop.order_id)
        self._stops.soft_delete(stop, current_user.id)
        self._timeline.record(
            current_user,
            stop.order_id,
            "STOP_REMOVED",
            f"Stop sequence {stop.sequence} removed.",
        )
        self._audit.record_order_stop_removed(
            company_id=current_user.company_id,
            user_id=current_user.id,
            entity_id=str(stop.id),
            ip_address=ip_address,
        )
