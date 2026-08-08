"""Development database seeding."""

from sqlalchemy import select

import app.database.session as db_session_module
from app.auth.security import hash_password
from app.common.enums import UserRole
from app.companies.models import Company, CompanySettings
from app.config.settings import get_settings
from app.database.session import init_engine
from app.users.models import User


def seed_development_data() -> None:
    """Seed default company and admin user for local development."""
    settings = get_settings()
    if settings.environment != "development":
        return

    init_engine(settings)
    if db_session_module.SessionLocal is None:
        msg = "Database session factory has not been initialized."
        raise RuntimeError(msg)

    db = db_session_module.SessionLocal()
    try:
        existing_users = db.scalar(select(User.id).limit(1))
        if existing_users is not None:
            return

        company = Company(name=settings.seed_company_name)
        db.add(company)
        db.commit()
        db.refresh(company)

        company_settings = CompanySettings(company_id=company.id)
        db.add(company_settings)

        admin_user = User(
            company_id=company.id,
            first_name="Admin",
            last_name="User",
            email=settings.seed_admin_email.lower(),
            password_hash=hash_password(settings.seed_admin_password),
            role=UserRole.ADMIN,
            is_active=True,
        )
        dispatcher_user = User(
            company_id=company.id,
            first_name="Dispatch",
            last_name="User",
            email="dispatcher@example.com",
            password_hash=hash_password("Dispatch123!"),
            role=UserRole.DISPATCHER,
            is_active=True,
        )
        db.add_all([admin_user, dispatcher_user])
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    seed_development_data()
