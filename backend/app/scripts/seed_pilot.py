"""Pilot customer onboarding seed — company shell without demo orders."""

from __future__ import annotations

import logging

from sqlalchemy import select

import app.database.session as db_session_module
from app.auth.security import hash_password
from app.common.enums import UserRole
from app.companies.models import Company, CompanySettings
from app.config.settings import get_settings
from app.database.session import init_engine
from app.users.models import User

logger = logging.getLogger(__name__)


def seed_pilot_data(*, force: bool = False) -> None:
    """Create a pilot company with admin user and default settings."""
    settings = get_settings()
    init_engine(settings)
    if db_session_module.SessionLocal is None:
        raise RuntimeError("Database session factory has not been initialized.")

    db = db_session_module.SessionLocal()
    try:
        existing = db.scalar(select(User.id).limit(1))
        if existing is not None and not force:
            logger.info("Pilot seed skipped because users already exist.")
            return

        company_name = settings.seed_company_name or "ProDrive Pilot Transport"
        company = Company(name=company_name)
        db.add(company)
        db.commit()
        db.refresh(company)
        db.add(CompanySettings(company_id=company.id))

        admin = User(
            company_id=company.id,
            first_name="Pilot",
            last_name="Admin",
            email=settings.seed_admin_email.lower(),
            password_hash=hash_password(settings.seed_admin_password),
            role=UserRole.ADMIN,
            is_active=True,
        )
        db.add(admin)
        db.commit()
        logger.info("Pilot seed completed for company %s", company.name)
    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    seed_pilot_data(force=True)
