"""Ensure production-style beta QA accounts exist for field testing."""

from __future__ import annotations

import logging

from sqlalchemy import func, select

import app.database.session as db_session_module
from app.auth.security import hash_password
from app.common.enums import OrderStatus, UserRole
from app.companies.models import Company
from app.config.settings import get_settings
from app.customers.models import Customer  # noqa: F401 — register FK metadata
from app.database.session import init_engine
from app.drivers.models import Driver
from app.orders.models import Order
from app.trailers.models import Trailer
from app.trucks.models import Truck
from app.users.models import User
from app.workflow.validators import ACTIVE_WORKFLOW_STATUSES

logger = logging.getLogger(__name__)

# Documented in docs/BETA_TEST_USERS.md — demo/testing only.
BETA_DRIVER_USERNAME = "VADYMSENIV"
BETA_DRIVER_EMAIL = "vadymseniv@prodrive.demo"
BETA_DRIVER_PASSWORD = "2JLH953"

BETA_DISPATCHER_USERNAME = "SASHABOX"
BETA_DISPATCHER_EMAIL = "sashabox@prodrive.demo"
BETA_DISPATCHER_PASSWORD = "BOX2026"

ACTIVE_STATUS_VALUES = {status.value for status in ACTIVE_WORKFLOW_STATUSES}


def _ensure_user(
    db,
    *,
    company_id,
    email: str,
    password: str,
    first_name: str,
    last_name: str,
    role: UserRole,
) -> User:
    """Create or refresh a user account with the given role."""
    normalized_email = email.lower()
    user = db.scalar(
        select(User).where(User.company_id == company_id, User.email == normalized_email)
    )
    password_hash = hash_password(password)
    if user is None:
        user = User(
            company_id=company_id,
            first_name=first_name,
            last_name=last_name,
            email=normalized_email,
            password_hash=password_hash,
            role=role,
            is_active=True,
        )
        db.add(user)
        db.flush()
        logger.info("Created beta test user %s (%s)", normalized_email, role.value)
    else:
        user.first_name = first_name
        user.last_name = last_name
        user.password_hash = password_hash
        user.role = role
        user.is_active = True
        logger.info("Refreshed beta test user %s (%s)", normalized_email, role.value)
    return user


def _ensure_driver_profile(db, *, company_id, user: User) -> Driver:
    """Create or refresh the driver profile linked to the user."""
    driver = db.scalar(
        select(Driver).where(
            Driver.company_id == company_id,
            Driver.user_id == user.id,
            Driver.deleted_at.is_(None),
        )
    )
    if driver is None:
        driver = Driver(
            company_id=company_id,
            user_id=user.id,
            phone="+32470987654",
            active=True,
        )
        db.add(driver)
        db.flush()
        logger.info("Created driver profile for %s", user.email)
    else:
        driver.active = True
    return driver


def _ensure_active_assignment(db, *, company_id, driver: Driver) -> str | None:
    """Assign an active workflow order when the driver has none."""
    active_count = int(
        db.scalar(
            select(func.count())
            .select_from(Order)
            .where(
                Order.company_id == company_id,
                Order.assigned_driver_id == driver.id,
                Order.status.in_(ACTIVE_STATUS_VALUES),
                Order.deleted_at.is_(None),
            )
        )
        or 0
    )
    if active_count > 0:
        order = db.scalar(
            select(Order)
            .where(
                Order.company_id == company_id,
                Order.assigned_driver_id == driver.id,
                Order.status.in_(ACTIVE_STATUS_VALUES),
                Order.deleted_at.is_(None),
            )
            .order_by(Order.created_at.asc())
            .limit(1)
        )
        return order.order_number if order else None

    order = db.scalar(
        select(Order)
        .where(
            Order.company_id == company_id,
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
        return None

    order.assigned_driver_id = driver.id
    if OrderStatus(order.status) in {OrderStatus.READY, OrderStatus.DRAFT}:
        order.status = OrderStatus.ASSIGNED.value
    logger.info("Assigned order %s to beta driver %s", order.order_number, driver.id)
    return order.order_number


def _ensure_beta_test_users_in_session(db, *, company_id) -> dict[str, object]:
    """Create or refresh beta QA users using an existing database session."""
    company = db.scalar(select(Company).where(Company.id == company_id))
    if company is None:
        raise RuntimeError("No company found — run seed_dev first.")

    driver_user = _ensure_user(
        db,
        company_id=company.id,
        email=BETA_DRIVER_EMAIL,
        password=BETA_DRIVER_PASSWORD,
        first_name="Vadym",
        last_name="Seniv",
        role=UserRole.DRIVER,
    )
    driver = _ensure_driver_profile(db, company_id=company.id, user=driver_user)

    dispatcher_user = _ensure_user(
        db,
        company_id=company.id,
        email=BETA_DISPATCHER_EMAIL,
        password=BETA_DISPATCHER_PASSWORD,
        first_name="Sasha",
        last_name="Box",
        role=UserRole.DISPATCHER,
    )

    sample_order_number = _ensure_active_assignment(
        db,
        company_id=company.id,
        driver=driver,
    )

    db.commit()

    result = {
        "driver": {
            "username": BETA_DRIVER_USERNAME,
            "email": BETA_DRIVER_EMAIL,
            "user_id": str(driver_user.id),
            "driver_id": str(driver.id),
            "role": UserRole.DRIVER.value,
            "sample_order_number": sample_order_number,
        },
        "dispatcher": {
            "username": BETA_DISPATCHER_USERNAME,
            "email": BETA_DISPATCHER_EMAIL,
            "user_id": str(dispatcher_user.id),
            "role": UserRole.DISPATCHER.value,
        },
    }
    logger.info(
        "Beta test users ready — driver=%s dispatcher=%s",
        BETA_DRIVER_EMAIL,
        BETA_DISPATCHER_EMAIL,
    )
    return result


def ensure_beta_test_users(*, company_id=None, db=None) -> dict[str, object]:
    """Create or refresh the canonical beta QA driver and dispatcher accounts."""
    if db is not None:
        if company_id is None:
            company = db.scalar(select(Company).order_by(Company.created_at.asc()).limit(1))
            if company is None:
                raise RuntimeError("No company found — run seed_dev first.")
            company_id = company.id
        return _ensure_beta_test_users_in_session(db, company_id=company_id)

    settings = get_settings()
    init_engine(settings)
    if db_session_module.SessionLocal is None:
        msg = "Database session factory has not been initialized."
        raise RuntimeError(msg)

    session = db_session_module.SessionLocal()
    try:
        if company_id is None:
            company = session.scalar(select(Company).order_by(Company.created_at.asc()).limit(1))
            if company is None:
                raise RuntimeError("No company found — run seed_dev first.")
            company_id = company.id
        return _ensure_beta_test_users_in_session(session, company_id=company_id)
    finally:
        session.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    summary = ensure_beta_test_users()
    print("BETA_TEST_USERS", summary)
