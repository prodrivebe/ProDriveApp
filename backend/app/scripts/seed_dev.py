"""Development database seeding."""

from __future__ import annotations

import argparse
import logging

from sqlalchemy import select

import app.database.session as db_session_module
from app.auth.security import hash_password
from app.common.enums import UserRole
from app.companies.models import Company, CompanySettings
from app.config.settings import get_settings
from app.database.session import init_engine
from app.scripts.demo_data import (
    DEMO_ADMIN_EMAIL,
    DEMO_ADMIN_PASSWORD,
    DEMO_COMPANY_NAME,
    DEMO_DISPATCHER_EMAIL,
    DEMO_DISPATCHER_PASSWORD,
    count_demo_entities,
    ensure_demo_lookup_data,
)
from app.users.models import User

logger = logging.getLogger(__name__)


def seed_development_data(*, reset: bool = True) -> None:
    """Seed demo company, QA users, and Belgian lookup data for local development."""
    settings = get_settings()
    if settings.environment != "development":
        return

    init_engine(settings)
    if db_session_module.SessionLocal is None:
        msg = "Database session factory has not been initialized."
        raise RuntimeError(msg)

    db = db_session_module.SessionLocal()
    try:
        company = db.scalar(select(Company).order_by(Company.created_at.asc()).limit(1))
        if company is None:
            company = Company(name=settings.seed_company_name or DEMO_COMPANY_NAME)
            db.add(company)
            db.commit()
            db.refresh(company)
            db.add(CompanySettings(company_id=company.id))
            db.commit()

        # Legacy dev accounts kept for backward compatibility with existing docs/tests.
        legacy_admin = db.scalar(
            select(User).where(
                User.company_id == company.id,
                User.email == settings.seed_admin_email.lower(),
            )
        )
        if legacy_admin is None and settings.seed_admin_email.lower() != DEMO_ADMIN_EMAIL.lower():
            db.add(
                User(
                    company_id=company.id,
                    first_name="Admin",
                    last_name="User",
                    email=settings.seed_admin_email.lower(),
                    password_hash=hash_password(settings.seed_admin_password),
                    role=UserRole.ADMIN,
                    is_active=True,
                )
            )

        legacy_dispatcher = db.scalar(
            select(User).where(
                User.company_id == company.id,
                User.email == "dispatcher@example.com",
            )
        )
        if legacy_dispatcher is None and DEMO_DISPATCHER_EMAIL.lower() != "dispatcher@example.com":
            db.add(
                User(
                    company_id=company.id,
                    first_name="Dispatch",
                    last_name="User",
                    email="dispatcher@example.com",
                    password_hash=hash_password("Dispatch123!"),
                    role=UserRole.DISPATCHER,
                    is_active=True,
                )
            )

        db.commit()
        ensure_demo_lookup_data(db, company.id, reset=reset)

        from app.scripts.ensure_beta_test_users import ensure_beta_test_users
        from app.scripts.ensure_mobile_demo_driver import ensure_mobile_demo_driver

        ensure_mobile_demo_driver(company_id=company.id)
        ensure_beta_test_users(company_id=company.id)

        counts = count_demo_entities(db, company.id)
        logger.info(
            "Development seed completed for %s — customers=%d drivers=%d trucks=%d trailers=%d orders=%d",
            company.name,
            counts["customers"],
            counts["drivers"],
            counts["trucks"],
            counts["trailers"],
            counts["orders"],
        )
        logger.info("Demo admin login: %s / %s", DEMO_ADMIN_EMAIL, DEMO_ADMIN_PASSWORD)
        logger.info("Demo dispatcher login: %s / %s", DEMO_DISPATCHER_EMAIL, DEMO_DISPATCHER_PASSWORD)
        logger.info("Mobile driver login: driver1@prodrive.demo / ProDrive2026!")
        logger.info(
            "Beta field driver login: vadymseniv@prodrive.demo / (see docs/BETA_TEST_USERS.md)"
        )
        logger.info(
            "Beta field dispatcher login: sashabox@prodrive.demo / (see docs/BETA_TEST_USERS.md)"
        )
    finally:
        db.close()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed ProDrive development demo data.")
    parser.add_argument(
        "--no-reset",
        action="store_true",
        help="Skip wiping operational/lookup data before seeding (append-only legacy mode).",
    )
    return parser.parse_args()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    args = _parse_args()
    seed_development_data(reset=not args.no_reset)
