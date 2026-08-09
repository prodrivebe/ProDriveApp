"""CSV import tools for pilot onboarding."""

from __future__ import annotations

import argparse
import csv
import logging
import uuid
from decimal import Decimal
from pathlib import Path

from sqlalchemy import select

import app.database.session as db_session_module
from app.auth.security import hash_password
from app.common.enums import UserRole
from app.companies.models import Company
from app.config.settings import get_settings
from app.customers.models import Customer
from app.database.session import init_engine
from app.drivers.models import Driver
from app.trailers.models import Trailer
from app.trucks.models import Truck
from app.users.models import User

logger = logging.getLogger(__name__)


def _get_company(db, company_id: uuid.UUID | None) -> Company:
    if company_id is not None:
        company = db.get(Company, company_id)
        if company is None:
            raise ValueError(f"Company not found: {company_id}")
        return company
    company = db.scalar(select(Company).limit(1))
    if company is None:
        raise ValueError("No company exists. Run pilot seed first.")
    return company


def import_customers(path: Path, company_id: uuid.UUID | None) -> int:
    settings = get_settings()
    init_engine(settings)
    if db_session_module.SessionLocal is None:
        raise RuntimeError("Database session factory has not been initialized.")
    db = db_session_module.SessionLocal()
    created = 0
    try:
        company = _get_company(db, company_id)
        with path.open(newline="", encoding="utf-8-sig") as handle:
            for row in csv.DictReader(handle):
                customer = Customer(
                    company_id=company.id,
                    company_name=row["company_name"].strip(),
                    vat_number=row.get("vat_number") or None,
                    address=row.get("address") or None,
                    city=row.get("city") or None,
                    country=row.get("country") or None,
                    email=row.get("email") or None,
                    phone=row.get("phone") or None,
                    notes=row.get("notes") or None,
                )
                db.add(customer)
                created += 1
        db.commit()
    finally:
        db.close()
    return created


def import_trucks(path: Path, company_id: uuid.UUID | None) -> int:
    settings = get_settings()
    init_engine(settings)
    if db_session_module.SessionLocal is None:
        raise RuntimeError("Database session factory has not been initialized.")
    db = db_session_module.SessionLocal()
    created = 0
    try:
        company = _get_company(db, company_id)
        with path.open(newline="", encoding="utf-8-sig") as handle:
            for row in csv.DictReader(handle):
                truck = Truck(
                    company_id=company.id,
                    registration_number=row["registration_number"].strip(),
                    brand=row.get("brand") or None,
                    model=row.get("model") or None,
                    vin=row.get("vin") or None,
                    capacity=int(row["capacity"]) if row.get("capacity") else None,
                    active=(row.get("active", "true").lower() != "false"),
                )
                db.add(truck)
                created += 1
        db.commit()
    finally:
        db.close()
    return created


def import_trailers(path: Path, company_id: uuid.UUID | None) -> int:
    settings = get_settings()
    init_engine(settings)
    if db_session_module.SessionLocal is None:
        raise RuntimeError("Database session factory has not been initialized.")
    db = db_session_module.SessionLocal()
    created = 0
    try:
        company = _get_company(db, company_id)
        with path.open(newline="", encoding="utf-8-sig") as handle:
            for row in csv.DictReader(handle):
                trailer = Trailer(
                    company_id=company.id,
                    registration_number=row["registration_number"].strip(),
                    manufacturer=row.get("manufacturer") or None,
                    model=row.get("model") or None,
                    trailer_type=row.get("trailer_type") or None,
                    maximum_height=Decimal(row["maximum_height"]) if row.get("maximum_height") else None,
                    maximum_weight=Decimal(row["maximum_weight"]) if row.get("maximum_weight") else None,
                    maximum_vehicle_count=int(row.get("maximum_vehicle_count") or 5),
                    active=(row.get("active", "true").lower() != "false"),
                )
                db.add(trailer)
                created += 1
        db.commit()
    finally:
        db.close()
    return created


def import_drivers(path: Path, company_id: uuid.UUID | None, default_password: str) -> int:
    settings = get_settings()
    init_engine(settings)
    if db_session_module.SessionLocal is None:
        raise RuntimeError("Database session factory has not been initialized.")
    db = db_session_module.SessionLocal()
    created = 0
    try:
        company = _get_company(db, company_id)
        with path.open(newline="", encoding="utf-8-sig") as handle:
            for row in csv.DictReader(handle):
                user = User(
                    company_id=company.id,
                    first_name=row["first_name"].strip(),
                    last_name=row["last_name"].strip(),
                    email=row["email"].strip().lower(),
                    password_hash=hash_password(row.get("password") or default_password),
                    role=UserRole.DRIVER,
                    is_active=(row.get("active", "true").lower() != "false"),
                )
                db.add(user)
                db.flush()
                driver = Driver(
                    company_id=company.id,
                    user_id=user.id,
                    phone=row.get("phone") or None,
                    active=user.is_active,
                )
                db.add(driver)
                created += 1
        db.commit()
    finally:
        db.close()
    return created


def main() -> None:
    parser = argparse.ArgumentParser(description="Import pilot CSV data into ProDrive.")
    parser.add_argument("entity", choices=["customers", "drivers", "trucks", "trailers"])
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--company-id", type=uuid.UUID, default=None)
    parser.add_argument("--default-password", default="ChangeMe123!")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    if args.entity == "customers":
        count = import_customers(args.csv_path, args.company_id)
    elif args.entity == "drivers":
        count = import_drivers(args.csv_path, args.company_id, args.default_password)
    elif args.entity == "trucks":
        count = import_trucks(args.csv_path, args.company_id)
    else:
        count = import_trailers(args.csv_path, args.company_id)
    logger.info("Imported %s %s records from %s", count, args.entity, args.csv_path)


if __name__ == "__main__":
    main()
