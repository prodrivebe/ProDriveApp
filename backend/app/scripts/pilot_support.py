"""Admin support tools for pilot operations."""

from __future__ import annotations

import argparse
import logging
import uuid

from sqlalchemy import select

import app.database.session as db_session_module
from app.auth.security import hash_password
from app.companies.models import Company
from app.config.settings import get_settings
from app.database.session import init_engine
from app.users.models import User

logger = logging.getLogger(__name__)


def list_users(company_id: uuid.UUID | None) -> list[User]:
    settings = get_settings()
    init_engine(settings)
    if db_session_module.SessionLocal is None:
        raise RuntimeError("Database session factory has not been initialized.")
    db = db_session_module.SessionLocal()
    try:
        query = select(User).order_by(User.email)
        if company_id is not None:
            query = query.where(User.company_id == company_id)
        return list(db.scalars(query).all())
    finally:
        db.close()


def reset_password(email: str, new_password: str) -> None:
    settings = get_settings()
    init_engine(settings)
    if db_session_module.SessionLocal is None:
        raise RuntimeError("Database session factory has not been initialized.")
    db = db_session_module.SessionLocal()
    try:
        user = db.scalar(select(User).where(User.email == email.lower()))
        if user is None:
            raise ValueError(f"User not found: {email}")
        user.password_hash = hash_password(new_password)
        db.commit()
        logger.info("Password reset for %s", email)
    finally:
        db.close()


def show_company_summary(company_id: uuid.UUID | None) -> Company:
    settings = get_settings()
    init_engine(settings)
    if db_session_module.SessionLocal is None:
        raise RuntimeError("Database session factory has not been initialized.")
    db = db_session_module.SessionLocal()
    try:
        if company_id is not None:
            company = db.get(Company, company_id)
        else:
            company = db.scalar(select(Company).limit(1))
        if company is None:
            raise ValueError("Company not found.")
        return company
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="ProDrive pilot support tools.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list-users")
    list_parser.add_argument("--company-id", type=uuid.UUID, default=None)

    reset_parser = subparsers.add_parser("reset-password")
    reset_parser.add_argument("email")
    reset_parser.add_argument("new_password")

    summary_parser = subparsers.add_parser("company-summary")
    summary_parser.add_argument("--company-id", type=uuid.UUID, default=None)

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)

    if args.command == "list-users":
        users = list_users(args.company_id)
        for user in users:
            print(f"{user.email}\t{user.role.value}\tactive={user.is_active}\tid={user.id}")
    elif args.command == "reset-password":
        reset_password(args.email, args.new_password)
    else:
        company = show_company_summary(args.company_id)
        print(f"{company.id}\t{company.name}")


if __name__ == "__main__":
    main()
