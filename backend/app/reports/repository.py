"""Report persistence layer."""

import uuid

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.common.enums import OrderStatus
from app.customers.models import Customer
from app.drivers.models import Driver
from app.orders.models import Order
from app.trailers.models import Trailer
from app.trucks.models import Truck
from app.users.models import User


class ReportRepository:
    """Repository for aggregated report queries."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def order_counts_by_status(self, company_id: uuid.UUID) -> dict[str, int]:
        """Return order counts grouped by status."""
        statement = (
            select(Order.status, func.count())
            .where(Order.company_id == company_id, Order.deleted_at.is_(None))
            .group_by(Order.status)
        )
        rows = self._db.execute(statement).all()
        return {status: int(count) for status, count in rows}

    def driver_activity(self, company_id: uuid.UUID) -> list[tuple]:
        """Return driver activity aggregates joined with user names."""
        assigned = func.count(Order.id)
        completed = func.sum(
            case((Order.status == OrderStatus.COMPLETED, 1), else_=0)
        )
        active = func.sum(
            case(
                (
                    Order.status.in_(
                        [
                            OrderStatus.ASSIGNED,
                            OrderStatus.ACCEPTED,
                            OrderStatus.LOADING,
                            OrderStatus.IN_TRANSIT,
                            OrderStatus.DELIVERING,
                        ]
                    ),
                    1,
                ),
                else_=0,
            )
        )
        statement = (
            select(
                Driver.id,
                User.first_name,
                User.last_name,
                assigned,
                completed,
                active,
            )
            .join(User, User.id == Driver.user_id)
            .outerjoin(
                Order,
                (Order.assigned_driver_id == Driver.id)
                & (Order.deleted_at.is_(None))
                & (Order.company_id == company_id),
            )
            .where(Driver.company_id == company_id, Driver.deleted_at.is_(None))
            .group_by(Driver.id, User.first_name, User.last_name)
            .order_by(assigned.desc())
        )
        return list(self._db.execute(statement).all())

    def customer_activity(self, company_id: uuid.UUID) -> list[tuple]:
        """Return customer activity aggregates."""
        total_orders = func.count(Order.id)
        completed_orders = func.sum(
            case((Order.status == OrderStatus.COMPLETED, 1), else_=0)
        )
        statement = (
            select(
                Customer.id,
                Customer.company_name,
                total_orders,
                completed_orders,
            )
            .outerjoin(
                Order,
                (Order.customer_id == Customer.id)
                & (Order.deleted_at.is_(None))
                & (Order.company_id == company_id),
            )
            .where(Customer.company_id == company_id, Customer.deleted_at.is_(None))
            .group_by(Customer.id, Customer.company_name)
            .order_by(total_orders.desc())
        )
        return list(self._db.execute(statement).all())

    def count_customers(self, company_id: uuid.UUID) -> int:
        """Return total active customers."""
        return int(
            self._db.scalar(
                select(func.count())
                .select_from(Customer)
                .where(Customer.company_id == company_id, Customer.deleted_at.is_(None))
            )
            or 0
        )

    def count_assigned_fleet(self, company_id: uuid.UUID) -> tuple[int, int, int]:
        """Return counts of fleet resources currently assigned to active orders."""
        active_statuses = [
            OrderStatus.ASSIGNED,
            OrderStatus.ACCEPTED,
            OrderStatus.LOADING,
            OrderStatus.IN_TRANSIT,
            OrderStatus.DELIVERING,
        ]
        base_filters = [
            Order.company_id == company_id,
            Order.deleted_at.is_(None),
            Order.status.in_(active_statuses),
        ]
        drivers = int(
            self._db.scalar(
                select(func.count(func.distinct(Order.assigned_driver_id))).where(
                    *base_filters,
                    Order.assigned_driver_id.is_not(None),
                )
            )
            or 0
        )
        trucks = int(
            self._db.scalar(
                select(func.count(func.distinct(Order.assigned_truck_id))).where(
                    *base_filters,
                    Order.assigned_truck_id.is_not(None),
                )
            )
            or 0
        )
        trailers = int(
            self._db.scalar(
                select(func.count(func.distinct(Order.assigned_trailer_id))).where(
                    *base_filters,
                    Order.assigned_trailer_id.is_not(None),
                )
            )
            or 0
        )
        return drivers, trucks, trailers
