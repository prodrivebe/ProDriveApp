"""Beta demonstration dataset for transport company pilots."""

from __future__ import annotations

import logging
from datetime import date, timedelta

from sqlalchemy import select

import app.database.session as db_session_module
from app.auth.security import hash_password
from app.common.enums import OrderStatus, UserRole
from app.companies.models import Company, CompanySettings
from app.config.settings import get_settings
from app.customers.models import Customer
from app.database.session import init_engine
from app.drivers.models import Driver
from app.orders.models import Order, OrderStop, OrderVehicle
from app.trailers.models import Trailer
from app.trucks.models import Truck
from app.users.models import User

logger = logging.getLogger(__name__)


def seed_beta_data(*, force: bool = False) -> None:
    """Seed a realistic beta dataset when the database is empty or force=True."""
    settings = get_settings()
    init_engine(settings)
    if db_session_module.SessionLocal is None:
        raise RuntimeError("Database session factory has not been initialized.")

    db = db_session_module.SessionLocal()
    try:
        existing = db.scalar(select(User.id).limit(1))
        if existing is not None and not force:
            logger.info("Beta seed skipped because users already exist.")
            return

        company = Company(name=settings.seed_company_name or "ProDrive Beta Transport")
        db.add(company)
        db.commit()
        db.refresh(company)
        db.add(CompanySettings(company_id=company.id))

        admin = User(
            company_id=company.id,
            first_name="Beta",
            last_name="Admin",
            email=settings.seed_admin_email.lower(),
            password_hash=hash_password(settings.seed_admin_password),
            role=UserRole.ADMIN,
            is_active=True,
        )
        dispatcher = User(
            company_id=company.id,
            first_name="Beta",
            last_name="Dispatcher",
            email="dispatcher@beta.local",
            password_hash=hash_password("Dispatch123!"),
            role=UserRole.DISPATCHER,
            is_active=True,
        )
        driver_users = []
        for index, name in enumerate(["John", "Maria"], start=1):
            driver_users.append(
                User(
                    company_id=company.id,
                    first_name=name,
                    last_name="Driver",
                    email=f"driver{index}@beta.local",
                    password_hash=hash_password("Driver123!"),
                    role=UserRole.DRIVER,
                    is_active=True,
                )
            )
        db.add_all([admin, dispatcher, *driver_users])
        db.commit()
        for user in driver_users:
            db.refresh(user)

        drivers = [
            Driver(company_id=company.id, user_id=user.id, phone=f"+316000000{index}", active=True)
            for index, user in enumerate(driver_users, start=1)
        ]
        trucks = [
            Truck(
                company_id=company.id,
                registration_number="BT-TRUCK-01",
                make="Volvo",
                model="FH",
                active=True,
            ),
            Truck(
                company_id=company.id,
                registration_number="BT-TRUCK-02",
                make="Scania",
                model="R450",
                active=True,
            ),
        ]
        trailers = [
            Trailer(
                company_id=company.id,
                registration_number="BT-TRAILER-01",
                maximum_vehicle_count=5,
                maximum_height=4.0,
                maximum_weight=20000,
                trailer_type="car_carrier",
                active=True,
            ),
            Trailer(
                company_id=company.id,
                registration_number="BT-TRAILER-02",
                maximum_vehicle_count=3,
                maximum_height=3.8,
                maximum_weight=12000,
                trailer_type="car_carrier",
                active=True,
            ),
        ]
        db.add_all([*drivers, *trucks, *trailers])
        db.commit()
        for item in drivers:
            db.refresh(item)

        customers = [
            Customer(company_id=company.id, company_name="ACME Auto Logistics", city="Amsterdam"),
            Customer(company_id=company.id, company_name="EuroCar Imports", city="Rotterdam"),
            Customer(company_id=company.id, company_name="Nordic Motors BV", city="Utrecht"),
        ]
        db.add_all(customers)
        db.commit()
        for customer in customers:
            db.refresh(customer)

        today = date.today()
        order_specs = [
            (OrderStatus.READY, customers[0], "BT-2026-001"),
            (OrderStatus.ASSIGNED, customers[1], "BT-2026-002"),
            (OrderStatus.LOADING, customers[2], "BT-2026-003"),
            (OrderStatus.IN_TRANSIT, customers[0], "BT-2026-004"),
            (OrderStatus.COMPLETED, customers[1], "BT-2026-005"),
        ]
        for index, (status, customer, order_number) in enumerate(order_specs):
            order = Order(
                company_id=company.id,
                customer_id=customer.id,
                order_number=order_number,
                status=status.value,
                planned_pickup_date=today + timedelta(days=index),
                planned_delivery_date=today + timedelta(days=index + 2),
                assigned_driver_id=drivers[0].id if status != OrderStatus.READY else None,
                assigned_truck_id=trucks[0].id if status not in {OrderStatus.READY} else None,
                assigned_trailer_id=trailers[0].id if status not in {OrderStatus.READY} else None,
                notes="Beta seed order",
            )
            db.add(order)
            db.flush()
            db.add_all(
                [
                    OrderStop(
                        company_id=company.id,
                        order_id=order.id,
                        stop_type="PICKUP",
                        sequence=1,
                        city="Amsterdam",
                        country="NL",
                    ),
                    OrderStop(
                        company_id=company.id,
                        order_id=order.id,
                        stop_type="DELIVERY",
                        sequence=2,
                        city="Brussels",
                        country="BE",
                    ),
                ]
            )
            db.add_all(
                [
                    OrderVehicle(
                        company_id=company.id,
                        order_id=order.id,
                        make="BMW",
                        model="X5",
                        estimated_weight=2200,
                        estimated_height=1.75,
                    ),
                    OrderVehicle(
                        company_id=company.id,
                        order_id=order.id,
                        make="Audi",
                        model="A4",
                        estimated_weight=1500,
                        estimated_height=1.45,
                    ),
                ]
            )
        db.commit()
        logger.info("Beta seed completed for company %s", company.name)
    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    seed_beta_data(force=True)
