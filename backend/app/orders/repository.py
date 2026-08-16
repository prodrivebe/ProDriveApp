"""Order persistence layer."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.common.enums import OrderStatus
from app.orders.models import Order
from app.orders.schemas import OrderCreateRequest, OrderUpdateRequest


class OrderRepository:
    """Repository for order records."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_id_for_company(
        self,
        order_id: uuid.UUID,
        company_id: uuid.UUID,
        *,
        with_details: bool = False,
    ) -> Order | None:
        """Return an order scoped to a company."""
        statement = select(Order).where(
            Order.id == order_id,
            Order.company_id == company_id,
            Order.deleted_at.is_(None),
        )
        if with_details:
            statement = statement.options(
                selectinload(Order.stops),
                selectinload(Order.vehicles),
            )
        return self._db.scalar(statement)

    def list_for_company(
        self,
        company_id: uuid.UUID,
        *,
        page: int,
        page_size: int,
        status: OrderStatus | None = None,
        customer_id: uuid.UUID | None = None,
        driver_id: uuid.UUID | None = None,
        search: str | None = None,
    ) -> tuple[list[Order], int]:
        """Return paginated orders for a company."""
        filters = [Order.company_id == company_id, Order.deleted_at.is_(None)]
        if status is not None:
            filters.append(Order.status == status)
        if customer_id is not None:
            filters.append(Order.customer_id == customer_id)
        if driver_id is not None:
            filters.append(Order.assigned_driver_id == driver_id)
        if search:
            pattern = f"%{search.strip()}%"
            filters.append(
                or_(
                    Order.order_number.ilike(pattern),
                    Order.notes.ilike(pattern),
                )
            )

        total = int(
            self._db.scalar(select(func.count()).select_from(Order).where(*filters)) or 0
        )
        statement = (
            select(Order)
            .where(*filters)
            .order_by(Order.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(self._db.scalars(statement).all()), total

    def count_for_company(self, company_id: uuid.UUID) -> int:
        """Return the number of orders for a company."""
        return int(
            self._db.scalar(
                select(func.count())
                .select_from(Order)
                .where(Order.company_id == company_id, Order.deleted_at.is_(None))
            )
            or 0
        )

    def create(
        self,
        *,
        company_id: uuid.UUID,
        customer_id: uuid.UUID,
        order_number: str,
        payload: OrderCreateRequest,
        created_by: uuid.UUID,
    ) -> Order:
        """Create an order record."""
        order = Order(
            company_id=company_id,
            customer_id=customer_id,
            order_number=order_number,
            status=OrderStatus.DRAFT,
            planned_pickup_date=payload.planned_pickup_date,
            planned_delivery_date=payload.planned_delivery_date,
            customer_reference_numbers=list(payload.customer_reference_numbers),
            notes=payload.notes,
            created_by=created_by,
            updated_by=created_by,
        )
        self._db.add(order)
        self._db.commit()
        self._db.refresh(order)
        return order

    def update(
        self,
        order: Order,
        payload: OrderUpdateRequest,
        updated_by: uuid.UUID,
    ) -> Order:
        """Update an order record."""
        order.customer_id = payload.customer_id
        order.planned_pickup_date = payload.planned_pickup_date
        order.planned_delivery_date = payload.planned_delivery_date
        if payload.customer_reference_numbers is not None:
            order.customer_reference_numbers = list(payload.customer_reference_numbers)
        order.notes = payload.notes
        if payload.status is not None:
            order.status = payload.status
        order.updated_by = updated_by
        self._db.add(order)
        self._db.commit()
        self._db.refresh(order)
        return order

    def update_status(
        self,
        order: Order,
        status: OrderStatus,
        updated_by: uuid.UUID,
        *,
        assigned_driver_id: uuid.UUID | None = None,
        assigned_truck_id: uuid.UUID | None = None,
        assigned_trailer_id: uuid.UUID | None = None,
        clear_assignment: bool = False,
    ) -> Order:
        """Update order status and optional assignment fields."""
        order.status = status
        order.updated_by = updated_by
        if clear_assignment:
            order.assigned_driver_id = None
            order.assigned_truck_id = None
            order.assigned_trailer_id = None
        else:
            if assigned_driver_id is not None:
                order.assigned_driver_id = assigned_driver_id
            if assigned_truck_id is not None:
                order.assigned_truck_id = assigned_truck_id
            if assigned_trailer_id is not None:
                order.assigned_trailer_id = assigned_trailer_id
        self._db.add(order)
        self._db.commit()
        self._db.refresh(order)
        return order

    def update_assignment(
        self,
        order: Order,
        updated_by: uuid.UUID,
        *,
        assigned_driver_id: uuid.UUID,
        assigned_truck_id: uuid.UUID | None,
        assigned_trailer_id: uuid.UUID | None,
    ) -> Order:
        """Update fleet assignment fields without changing order status."""
        order.assigned_driver_id = assigned_driver_id
        order.assigned_truck_id = assigned_truck_id
        order.assigned_trailer_id = assigned_trailer_id
        order.updated_by = updated_by
        self._db.add(order)
        self._db.commit()
        self._db.refresh(order)
        return order

    def soft_delete(self, order: Order, deleted_by: uuid.UUID) -> Order:
        """Soft delete an order record."""
        order.deleted_at = datetime.now(tz=UTC)
        order.updated_by = deleted_by
        self._db.add(order)
        self._db.commit()
        self._db.refresh(order)
        return order


from app.order_stops.repository import OrderStopRepository  # noqa: E402
from app.order_timeline.repository import OrderTimelineRepository  # noqa: E402
from app.order_vehicles.repository import OrderVehicleRepository  # noqa: E402

__all__ = [
    "OrderRepository",
    "OrderStopRepository",
    "OrderTimelineRepository",
    "OrderVehicleRepository",
]
