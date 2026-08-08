"""Global search persistence layer."""

import uuid

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.customers.models import Customer
from app.drivers.models import Driver
from app.orders.models import Order, OrderVehicle
from app.trucks.models import Truck
from app.users.models import User

SEARCH_LIMIT = 10


class SearchRepository:
    """Repository for global search queries."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def search_orders(self, company_id: uuid.UUID, query: str) -> list[Order]:
        """Search orders by number or notes."""
        pattern = f"%{query.strip()}%"
        statement = (
            select(Order)
            .where(
                Order.company_id == company_id,
                Order.deleted_at.is_(None),
                or_(Order.order_number.ilike(pattern), Order.notes.ilike(pattern)),
            )
            .order_by(Order.created_at.desc())
            .limit(SEARCH_LIMIT)
        )
        return list(self._db.scalars(statement).all())

    def search_customers(self, company_id: uuid.UUID, query: str) -> list[Customer]:
        """Search customers."""
        pattern = f"%{query.strip()}%"
        statement = (
            select(Customer)
            .where(
                Customer.company_id == company_id,
                Customer.deleted_at.is_(None),
                or_(
                    Customer.company_name.ilike(pattern),
                    Customer.vat_number.ilike(pattern),
                    Customer.email.ilike(pattern),
                    Customer.phone.ilike(pattern),
                ),
            )
            .order_by(Customer.company_name.asc())
            .limit(SEARCH_LIMIT)
        )
        return list(self._db.scalars(statement).all())

    def search_drivers(
        self,
        company_id: uuid.UUID,
        query: str,
    ) -> list[tuple[Driver, User]]:
        """Search drivers by user name or phone."""
        pattern = f"%{query.strip()}%"
        statement = (
            select(Driver, User)
            .join(User, User.id == Driver.user_id)
            .where(
                Driver.company_id == company_id,
                Driver.deleted_at.is_(None),
                or_(
                    User.first_name.ilike(pattern),
                    User.last_name.ilike(pattern),
                    User.email.ilike(pattern),
                    Driver.phone.ilike(pattern),
                    Driver.driving_license.ilike(pattern),
                ),
            )
            .limit(SEARCH_LIMIT)
        )
        return [(row[0], row[1]) for row in self._db.execute(statement).all()]

    def search_vehicles(self, company_id: uuid.UUID, query: str) -> list[OrderVehicle]:
        """Search vehicles by VIN, make, or model."""
        pattern = f"%{query.strip()}%"
        statement = (
            select(OrderVehicle)
            .where(
                OrderVehicle.company_id == company_id,
                OrderVehicle.deleted_at.is_(None),
                or_(
                    OrderVehicle.vin.ilike(pattern),
                    OrderVehicle.make.ilike(pattern),
                    OrderVehicle.model.ilike(pattern),
                ),
            )
            .limit(SEARCH_LIMIT)
        )
        return list(self._db.scalars(statement).all())

    def search_trucks_by_registration(
        self,
        company_id: uuid.UUID,
        query: str,
    ) -> list[Truck]:
        """Search trucks by registration number."""
        pattern = f"%{query.strip()}%"
        statement = (
            select(Truck)
            .where(
                Truck.company_id == company_id,
                Truck.deleted_at.is_(None),
                Truck.registration_number.ilike(pattern),
            )
            .limit(SEARCH_LIMIT)
        )
        return list(self._db.scalars(statement).all())
