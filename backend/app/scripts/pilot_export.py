"""Export tools for pilot support and compliance."""

from __future__ import annotations

import argparse
import csv
import json
import logging
import uuid
import zipfile
from pathlib import Path

from sqlalchemy import select

import app.database.session as db_session_module
from app.audit.models import AuditLog
from app.companies.models import Company
from app.config.settings import get_settings
from app.database.session import init_engine
from app.order_documents.models import OrderDocument
from app.orders.models import Order
from app.vehicle_photos.models import VehiclePhoto

logger = logging.getLogger(__name__)


def _resolve_company_id(db, company_id: uuid.UUID | None) -> uuid.UUID:
    if company_id is not None:
        return company_id
    company = db.scalar(select(Company).limit(1))
    if company is None:
        raise ValueError("No company exists.")
    return company.id


def export_orders_csv(output: Path, company_id: uuid.UUID | None) -> int:
    settings = get_settings()
    init_engine(settings)
    if db_session_module.SessionLocal is None:
        raise RuntimeError("Database session factory has not been initialized.")
    db = db_session_module.SessionLocal()
    count = 0
    try:
        resolved_company_id = _resolve_company_id(db, company_id)
        orders = db.scalars(
            select(Order).where(Order.company_id == resolved_company_id).order_by(Order.created_at)
        ).all()
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(
                [
                    "order_id",
                    "order_number",
                    "status",
                    "customer_id",
                    "planned_pickup_date",
                    "planned_delivery_date",
                    "created_at",
                ]
            )
            for order in orders:
                writer.writerow(
                    [
                        str(order.id),
                        order.order_number,
                        order.status,
                        str(order.customer_id) if order.customer_id else "",
                        order.planned_pickup_date,
                        order.planned_delivery_date,
                        order.created_at.isoformat(),
                    ]
                )
                count += 1
    finally:
        db.close()
    return count


def export_audit_json(output: Path, company_id: uuid.UUID | None, limit: int) -> int:
    settings = get_settings()
    init_engine(settings)
    if db_session_module.SessionLocal is None:
        raise RuntimeError("Database session factory has not been initialized.")
    db = db_session_module.SessionLocal()
    count = 0
    try:
        resolved_company_id = _resolve_company_id(db, company_id)
        logs = db.scalars(
            select(AuditLog)
            .where(AuditLog.company_id == resolved_company_id)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
        ).all()
        payload = [
            {
                "id": str(entry.id),
                "user_id": str(entry.user_id) if entry.user_id else None,
                "entity": entry.entity,
                "entity_id": entry.entity_id,
                "action": entry.action,
                "old_value": entry.old_value,
                "new_value": entry.new_value,
                "ip_address": entry.ip_address,
                "created_at": entry.created_at.isoformat(),
            }
            for entry in logs
        ]
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        count = len(payload)
    finally:
        db.close()
    return count


def export_documents_archive(output: Path, company_id: uuid.UUID | None, upload_root: Path) -> int:
    settings = get_settings()
    init_engine(settings)
    if db_session_module.SessionLocal is None:
        raise RuntimeError("Database session factory has not been initialized.")
    db = db_session_module.SessionLocal()
    copied = 0
    try:
        resolved_company_id = _resolve_company_id(db, company_id)
        documents = db.scalars(
            select(OrderDocument).where(OrderDocument.company_id == resolved_company_id)
        ).all()
        photos = db.scalars(
            select(VehiclePhoto).where(VehiclePhoto.company_id == resolved_company_id)
        ).all()
        output.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            manifest: list[dict[str, str]] = []
            for document in documents:
                source = upload_root / document.file_path
                if source.exists():
                    target_name = f"documents/{document.id}_{source.name}"
                    archive.write(source, arcname=target_name)
                    manifest.append({"type": "document", "id": str(document.id), "path": target_name})
                    copied += 1
            for photo in photos:
                source = upload_root / photo.file_path
                if source.exists():
                    target_name = f"photos/{photo.id}_{source.name}"
                    archive.write(source, arcname=target_name)
                    manifest.append({"type": "photo", "id": str(photo.id), "path": target_name})
                    copied += 1
            archive.writestr(
                "manifest.json",
                json.dumps(manifest, indent=2),
            )
    finally:
        db.close()
    return copied


def main() -> None:
    parser = argparse.ArgumentParser(description="Export pilot data from ProDrive.")
    parser.add_argument("target", choices=["orders", "audit", "documents"])
    parser.add_argument("output", type=Path)
    parser.add_argument("--company-id", type=uuid.UUID, default=None)
    parser.add_argument("--audit-limit", type=int, default=1000)
    parser.add_argument("--upload-root", type=Path, default=None)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    settings = get_settings()
    upload_root = args.upload_root or Path(settings.upload_root_dir)

    if args.target == "orders":
        count = export_orders_csv(args.output, args.company_id)
        logger.info("Exported %s orders to %s", count, args.output)
    elif args.target == "audit":
        count = export_audit_json(args.output, args.company_id, args.audit_limit)
        logger.info("Exported %s audit entries to %s", count, args.output)
    else:
        count = export_documents_archive(args.output, args.company_id, upload_root)
        logger.info("Archived %s files into %s", count, args.output)


if __name__ == "__main__":
    main()
