"""Ensure the canonical mobile app demo driver exists with an active assignment."""

from __future__ import annotations

import logging

from sqlalchemy import func, select

import app.database.session as db_session_module
from app.auth.security import hash_password
from app.common.enums import OrderStatus, StopType, UserRole
from app.companies.models import Company
from app.config.settings import get_settings
from app.customers.models import Customer  # noqa: F401 — register FK metadata
from app.database.session import init_engine
from app.drivers.models import Driver
from app.orders.models import Order, OrderStop
from app.trailers.models import Trailer
from app.trucks.models import Truck
from app.users.models import User
from app.workflow.validators import ACTIVE_WORKFLOW_STATUSES

logger = logging.getLogger(__name__)

DEMO_MOBILE_DRIVER_EMAIL = "driver1@prodrive.demo"
DEMO_MOBILE_DRIVER_PASSWORD = "ProDrive2026!"

ACTIVE_STATUS_VALUES = {status.value for status in ACTIVE_WORKFLOW_STATUSES}


def _normalize_order_stop_sequences(db, order_id) -> None:
    """Ensure pickup stops precede delivery stops when sequences collide."""
    stops = db.scalars(
        select(OrderStop).where(
            OrderStop.order_id == order_id,
            OrderStop.deleted_at.is_(None),
        )
    ).all()
    pickup_stops = [stop for stop in stops if stop.stop_type == StopType.PICKUP.value]
    delivery_stops = [stop for stop in stops if stop.stop_type == StopType.DELIVERY.value]
    for index, stop in enumerate(sorted(pickup_stops, key=lambda item: item.sequence), start=1):
        stop.sequence = index
    delivery_start = len(pickup_stops) + 1
    for offset, stop in enumerate(sorted(delivery_stops, key=lambda item: item.sequence)):
        stop.sequence = delivery_start + offset


def ensure_mobile_demo_driver(*, company_id=None) -> dict[str, object]:
    """Create or refresh the mobile demo driver and guarantee one active order."""
    settings = get_settings()
    init_engine(settings)
    if db_session_module.SessionLocal is None:
        msg = "Database session factory has not been initialized."
        raise RuntimeError(msg)

    db = db_session_module.SessionLocal()
    try:
        if company_id is None:
            company = db.scalar(select(Company).order_by(Company.created_at.asc()).limit(1))
        else:
            company = db.scalar(select(Company).where(Company.id == company_id))
        if company is None:
            raise RuntimeError("No company found — run seed_dev first.")

        email = DEMO_MOBILE_DRIVER_EMAIL.lower()
        user = db.scalar(
            select(User).where(User.company_id == company.id, User.email == email)
        )
        if user is None:
            user = User(
                company_id=company.id,
                first_name="Demo",
                last_name="Driver",
                email=email,
                password_hash=hash_password(DEMO_MOBILE_DRIVER_PASSWORD),
                role=UserRole.DRIVER,
                is_active=True,
            )
            db.add(user)
            db.flush()
            logger.info("Created mobile demo user %s", email)
        else:
            user.first_name = "Demo"
            user.last_name = "Driver"
            user.password_hash = hash_password(DEMO_MOBILE_DRIVER_PASSWORD)
            user.role = UserRole.DRIVER
            user.is_active = True
            logger.info("Refreshed mobile demo user %s", email)

        driver = db.scalar(
            select(Driver).where(
                Driver.company_id == company.id,
                Driver.user_id == user.id,
                Driver.deleted_at.is_(None),
            )
        )
        if driver is None:
            driver = Driver(
                company_id=company.id,
                user_id=user.id,
                phone="+32470123456",
                active=True,
            )
            db.add(driver)
            db.flush()
            logger.info("Created driver profile for %s", email)
        else:
            driver.active = True

        active_count = int(
            db.scalar(
                select(func.count())
                .select_from(Order)
                .where(
                    Order.company_id == company.id,
                    Order.assigned_driver_id == driver.id,
                    Order.status.in_(ACTIVE_STATUS_VALUES),
                    Order.deleted_at.is_(None),
                )
            )
            or 0
        )

        assigned_order_number: str | None = None
        if active_count == 0:
            order = db.scalar(
                select(Order)
                .where(
                    Order.company_id == company.id,
                    Order.deleted_at.is_(None),
                    Order.status.in_(
                        [
                            OrderStatus.READY.value,
                            OrderStatus.ASSIGNED.value,
                            OrderStatus.LOADING.value,
                        ]
                    ),
                )
                .order_by(Order.created_at.asc())
                .limit(1)
            )
            if order is None:
                order = db.scalar(
                    select(Order)
                    .where(Order.company_id == company.id, Order.deleted_at.is_(None))
                    .order_by(Order.created_at.asc())
                    .limit(1)
                )
            if order is None:
                raise RuntimeError("No orders in database — run seed_dev first.")

            truck = db.scalar(
                select(Truck)
                .where(Truck.company_id == company.id, Truck.active.is_(True), Truck.deleted_at.is_(None))
                .limit(1)
            )
            trailer = db.scalar(
                select(Trailer)
                .where(
                    Trailer.company_id == company.id,
                    Trailer.active.is_(True),
                    Trailer.deleted_at.is_(None),
                )
                .limit(1)
            )

            order.assigned_driver_id = driver.id
            if truck is not None:
                order.assigned_truck_id = truck.id
            if trailer is not None:
                order.assigned_trailer_id = trailer.id
            if OrderStatus(order.status) in {OrderStatus.READY, OrderStatus.DRAFT}:
                order.status = OrderStatus.ASSIGNED.value

            assigned_order_number = order.order_number
            active_count = 1
            logger.info(
                "Assigned order %s (%s) to mobile demo driver",
                order.order_number,
                order.status,
            )
        else:
            order = db.scalar(
                select(Order)
                .where(
                    Order.company_id == company.id,
                    Order.assigned_driver_id == driver.id,
                    Order.status.in_(ACTIVE_STATUS_VALUES),
                    Order.deleted_at.is_(None),
                )
                .order_by(Order.created_at.asc())
                .limit(1)
            )
            assigned_order_number = order.order_number if order else None

        if order is not None:
            _normalize_order_stop_sequences(db, order.id)

        db.commit()

        result = {
            "email": email,
            "password": DEMO_MOBILE_DRIVER_PASSWORD,
            "driver_id": str(driver.id),
            "active_orders": active_count,
            "sample_order_number": assigned_order_number,
        }
        logger.info(
            "Mobile demo driver ready — %s / %s — active_orders=%d sample=%s",
            email,
            DEMO_MOBILE_DRIVER_PASSWORD,
            active_count,
            assigned_order_number,
        )
        return result
    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    summary = ensure_mobile_demo_driver()
    print("MOBILE_DEMO_DRIVER", summary)
