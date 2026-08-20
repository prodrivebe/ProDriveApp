"""Truck operational record persistence layer."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.trucks.models import TruckInspectionRecord, TruckMaintenanceRecord, TruckTireRecord
from app.trucks.operational_schemas import (
    TruckInspectionRecordCreateRequest,
    TruckInspectionRecordUpdateRequest,
    TruckMaintenanceRecordCreateRequest,
    TruckMaintenanceRecordUpdateRequest,
    TruckTireRecordCreateRequest,
    TruckTireRecordUpdateRequest,
)


class TruckOperationalRepository:
    """Repository for truck maintenance, inspection, and tire records."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def list_maintenance_for_truck(
        self,
        truck_id: uuid.UUID,
        company_id: uuid.UUID,
    ) -> list[TruckMaintenanceRecord]:
        """Return maintenance records for a truck."""
        statement = (
            select(TruckMaintenanceRecord)
            .where(
                TruckMaintenanceRecord.truck_id == truck_id,
                TruckMaintenanceRecord.company_id == company_id,
                TruckMaintenanceRecord.deleted_at.is_(None),
            )
            .order_by(TruckMaintenanceRecord.maintenance_date.desc())
        )
        return list(self._db.scalars(statement).all())

    def get_maintenance_by_id(
        self,
        record_id: uuid.UUID,
        truck_id: uuid.UUID,
        company_id: uuid.UUID,
    ) -> TruckMaintenanceRecord | None:
        """Return a maintenance record scoped to a truck."""
        statement = select(TruckMaintenanceRecord).where(
            TruckMaintenanceRecord.id == record_id,
            TruckMaintenanceRecord.truck_id == truck_id,
            TruckMaintenanceRecord.company_id == company_id,
            TruckMaintenanceRecord.deleted_at.is_(None),
        )
        return self._db.scalar(statement)

    def create_maintenance(
        self,
        *,
        company_id: uuid.UUID,
        truck_id: uuid.UUID,
        payload: TruckMaintenanceRecordCreateRequest,
        created_by: uuid.UUID,
    ) -> TruckMaintenanceRecord:
        """Create a maintenance record."""
        record = TruckMaintenanceRecord(
            company_id=company_id,
            truck_id=truck_id,
            maintenance_date=payload.maintenance_date,
            mileage=payload.mileage,
            maintenance_type=payload.maintenance_type.strip(),
            notes=payload.notes,
            created_by=created_by,
            updated_by=created_by,
        )
        self._db.add(record)
        self._db.commit()
        self._db.refresh(record)
        return record

    def update_maintenance(
        self,
        record: TruckMaintenanceRecord,
        payload: TruckMaintenanceRecordUpdateRequest,
        updated_by: uuid.UUID,
    ) -> TruckMaintenanceRecord:
        """Update a maintenance record."""
        record.maintenance_date = payload.maintenance_date
        record.mileage = payload.mileage
        record.maintenance_type = payload.maintenance_type.strip()
        record.notes = payload.notes
        record.updated_by = updated_by
        self._db.add(record)
        self._db.commit()
        self._db.refresh(record)
        return record

    def soft_delete_maintenance(
        self,
        record: TruckMaintenanceRecord,
        deleted_by: uuid.UUID,
    ) -> TruckMaintenanceRecord:
        """Soft delete a maintenance record."""
        record.deleted_at = datetime.now(tz=UTC)
        record.updated_by = deleted_by
        self._db.add(record)
        self._db.commit()
        self._db.refresh(record)
        return record

    def list_inspections_for_truck(
        self,
        truck_id: uuid.UUID,
        company_id: uuid.UUID,
    ) -> list[TruckInspectionRecord]:
        """Return inspection records for a truck."""
        statement = (
            select(TruckInspectionRecord)
            .where(
                TruckInspectionRecord.truck_id == truck_id,
                TruckInspectionRecord.company_id == company_id,
                TruckInspectionRecord.deleted_at.is_(None),
            )
            .order_by(TruckInspectionRecord.inspection_date.desc())
        )
        return list(self._db.scalars(statement).all())

    def get_inspection_by_id(
        self,
        record_id: uuid.UUID,
        truck_id: uuid.UUID,
        company_id: uuid.UUID,
    ) -> TruckInspectionRecord | None:
        """Return an inspection record scoped to a truck."""
        statement = select(TruckInspectionRecord).where(
            TruckInspectionRecord.id == record_id,
            TruckInspectionRecord.truck_id == truck_id,
            TruckInspectionRecord.company_id == company_id,
            TruckInspectionRecord.deleted_at.is_(None),
        )
        return self._db.scalar(statement)

    def create_inspection(
        self,
        *,
        company_id: uuid.UUID,
        truck_id: uuid.UUID,
        payload: TruckInspectionRecordCreateRequest,
        created_by: uuid.UUID,
    ) -> TruckInspectionRecord:
        """Create an inspection record."""
        record = TruckInspectionRecord(
            company_id=company_id,
            truck_id=truck_id,
            inspection_date=payload.inspection_date,
            mileage=payload.mileage,
            inspection_type=payload.inspection_type.strip(),
            notes=payload.notes,
            created_by=created_by,
            updated_by=created_by,
        )
        self._db.add(record)
        self._db.commit()
        self._db.refresh(record)
        return record

    def update_inspection(
        self,
        record: TruckInspectionRecord,
        payload: TruckInspectionRecordUpdateRequest,
        updated_by: uuid.UUID,
    ) -> TruckInspectionRecord:
        """Update an inspection record."""
        record.inspection_date = payload.inspection_date
        record.mileage = payload.mileage
        record.inspection_type = payload.inspection_type.strip()
        record.notes = payload.notes
        record.updated_by = updated_by
        self._db.add(record)
        self._db.commit()
        self._db.refresh(record)
        return record

    def soft_delete_inspection(
        self,
        record: TruckInspectionRecord,
        deleted_by: uuid.UUID,
    ) -> TruckInspectionRecord:
        """Soft delete an inspection record."""
        record.deleted_at = datetime.now(tz=UTC)
        record.updated_by = deleted_by
        self._db.add(record)
        self._db.commit()
        self._db.refresh(record)
        return record

    def list_tires_for_truck(
        self,
        truck_id: uuid.UUID,
        company_id: uuid.UUID,
    ) -> list[TruckTireRecord]:
        """Return tire records for a truck."""
        statement = (
            select(TruckTireRecord)
            .where(
                TruckTireRecord.truck_id == truck_id,
                TruckTireRecord.company_id == company_id,
                TruckTireRecord.deleted_at.is_(None),
            )
            .order_by(TruckTireRecord.tire_date.desc())
        )
        return list(self._db.scalars(statement).all())

    def get_tire_by_id(
        self,
        record_id: uuid.UUID,
        truck_id: uuid.UUID,
        company_id: uuid.UUID,
    ) -> TruckTireRecord | None:
        """Return a tire record scoped to a truck."""
        statement = select(TruckTireRecord).where(
            TruckTireRecord.id == record_id,
            TruckTireRecord.truck_id == truck_id,
            TruckTireRecord.company_id == company_id,
            TruckTireRecord.deleted_at.is_(None),
        )
        return self._db.scalar(statement)

    def create_tire(
        self,
        *,
        company_id: uuid.UUID,
        truck_id: uuid.UUID,
        payload: TruckTireRecordCreateRequest,
        created_by: uuid.UUID,
    ) -> TruckTireRecord:
        """Create a tire record."""
        record = TruckTireRecord(
            company_id=company_id,
            truck_id=truck_id,
            tire_date=payload.tire_date,
            mileage=payload.mileage,
            tire_type=payload.tire_type.strip(),
            notes=payload.notes,
            created_by=created_by,
            updated_by=created_by,
        )
        self._db.add(record)
        self._db.commit()
        self._db.refresh(record)
        return record

    def update_tire(
        self,
        record: TruckTireRecord,
        payload: TruckTireRecordUpdateRequest,
        updated_by: uuid.UUID,
    ) -> TruckTireRecord:
        """Update a tire record."""
        record.tire_date = payload.tire_date
        record.mileage = payload.mileage
        record.tire_type = payload.tire_type.strip()
        record.notes = payload.notes
        record.updated_by = updated_by
        self._db.add(record)
        self._db.commit()
        self._db.refresh(record)
        return record

    def soft_delete_tire(
        self,
        record: TruckTireRecord,
        deleted_by: uuid.UUID,
    ) -> TruckTireRecord:
        """Soft delete a tire record."""
        record.deleted_at = datetime.now(tz=UTC)
        record.updated_by = deleted_by
        self._db.add(record)
        self._db.commit()
        self._db.refresh(record)
        return record
