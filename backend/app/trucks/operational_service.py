"""Truck operational record business logic."""

import uuid

from sqlalchemy.orm import Session

from app.common.exceptions import NotFoundError
from app.trucks.models import TruckInspectionRecord, TruckMaintenanceRecord, TruckTireRecord
from app.trucks.operational_repository import TruckOperationalRepository
from app.trucks.operational_schemas import (
    TruckInspectionRecordCreateRequest,
    TruckInspectionRecordUpdateRequest,
    TruckMaintenanceRecordCreateRequest,
    TruckMaintenanceRecordUpdateRequest,
    TruckTireRecordCreateRequest,
    TruckTireRecordUpdateRequest,
)
from app.trucks.service import TruckService
from app.users.models import User


class TruckOperationalService:
    """Truck maintenance, inspection, and tire record workflows."""

    def __init__(self, db: Session) -> None:
        self._db = db
        self._trucks = TruckService(db)
        self._repository = TruckOperationalRepository(db)

    def list_maintenance(
        self,
        current_user: User,
        truck_id: uuid.UUID,
    ) -> list[TruckMaintenanceRecord]:
        """List maintenance records for a truck."""
        self._trucks.get_truck(current_user, truck_id)
        return self._repository.list_maintenance_for_truck(truck_id, current_user.company_id)

    def create_maintenance(
        self,
        current_user: User,
        truck_id: uuid.UUID,
        payload: TruckMaintenanceRecordCreateRequest,
    ) -> TruckMaintenanceRecord:
        """Create a maintenance record for a truck."""
        self._trucks.get_truck(current_user, truck_id)
        return self._repository.create_maintenance(
            company_id=current_user.company_id,
            truck_id=truck_id,
            payload=payload,
            created_by=current_user.id,
        )

    def update_maintenance(
        self,
        current_user: User,
        truck_id: uuid.UUID,
        record_id: uuid.UUID,
        payload: TruckMaintenanceRecordUpdateRequest,
    ) -> TruckMaintenanceRecord:
        """Update a maintenance record."""
        record = self._get_maintenance(current_user, truck_id, record_id)
        return self._repository.update_maintenance(record, payload, current_user.id)

    def delete_maintenance(
        self,
        current_user: User,
        truck_id: uuid.UUID,
        record_id: uuid.UUID,
    ) -> None:
        """Soft delete a maintenance record."""
        record = self._get_maintenance(current_user, truck_id, record_id)
        self._repository.soft_delete_maintenance(record, current_user.id)

    def list_inspections(
        self,
        current_user: User,
        truck_id: uuid.UUID,
    ) -> list[TruckInspectionRecord]:
        """List inspection records for a truck."""
        self._trucks.get_truck(current_user, truck_id)
        return self._repository.list_inspections_for_truck(truck_id, current_user.company_id)

    def create_inspection(
        self,
        current_user: User,
        truck_id: uuid.UUID,
        payload: TruckInspectionRecordCreateRequest,
    ) -> TruckInspectionRecord:
        """Create an inspection record for a truck."""
        self._trucks.get_truck(current_user, truck_id)
        return self._repository.create_inspection(
            company_id=current_user.company_id,
            truck_id=truck_id,
            payload=payload,
            created_by=current_user.id,
        )

    def update_inspection(
        self,
        current_user: User,
        truck_id: uuid.UUID,
        record_id: uuid.UUID,
        payload: TruckInspectionRecordUpdateRequest,
    ) -> TruckInspectionRecord:
        """Update an inspection record."""
        record = self._get_inspection(current_user, truck_id, record_id)
        return self._repository.update_inspection(record, payload, current_user.id)

    def delete_inspection(
        self,
        current_user: User,
        truck_id: uuid.UUID,
        record_id: uuid.UUID,
    ) -> None:
        """Soft delete an inspection record."""
        record = self._get_inspection(current_user, truck_id, record_id)
        self._repository.soft_delete_inspection(record, current_user.id)

    def list_tires(
        self,
        current_user: User,
        truck_id: uuid.UUID,
    ) -> list[TruckTireRecord]:
        """List tire records for a truck."""
        self._trucks.get_truck(current_user, truck_id)
        return self._repository.list_tires_for_truck(truck_id, current_user.company_id)

    def create_tire(
        self,
        current_user: User,
        truck_id: uuid.UUID,
        payload: TruckTireRecordCreateRequest,
    ) -> TruckTireRecord:
        """Create a tire record for a truck."""
        self._trucks.get_truck(current_user, truck_id)
        return self._repository.create_tire(
            company_id=current_user.company_id,
            truck_id=truck_id,
            payload=payload,
            created_by=current_user.id,
        )

    def update_tire(
        self,
        current_user: User,
        truck_id: uuid.UUID,
        record_id: uuid.UUID,
        payload: TruckTireRecordUpdateRequest,
    ) -> TruckTireRecord:
        """Update a tire record."""
        record = self._get_tire(current_user, truck_id, record_id)
        return self._repository.update_tire(record, payload, current_user.id)

    def delete_tire(
        self,
        current_user: User,
        truck_id: uuid.UUID,
        record_id: uuid.UUID,
    ) -> None:
        """Soft delete a tire record."""
        record = self._get_tire(current_user, truck_id, record_id)
        self._repository.soft_delete_tire(record, current_user.id)

    def _get_maintenance(
        self,
        current_user: User,
        truck_id: uuid.UUID,
        record_id: uuid.UUID,
    ) -> TruckMaintenanceRecord:
        record = self._repository.get_maintenance_by_id(
            record_id,
            truck_id,
            current_user.company_id,
        )
        if record is None:
            raise NotFoundError(
                code="TRUCK_MAINTENANCE_NOT_FOUND",
                message="Truck maintenance record not found.",
            )
        return record

    def _get_inspection(
        self,
        current_user: User,
        truck_id: uuid.UUID,
        record_id: uuid.UUID,
    ) -> TruckInspectionRecord:
        record = self._repository.get_inspection_by_id(
            record_id,
            truck_id,
            current_user.company_id,
        )
        if record is None:
            raise NotFoundError(
                code="TRUCK_INSPECTION_NOT_FOUND",
                message="Truck inspection record not found.",
            )
        return record

    def _get_tire(
        self,
        current_user: User,
        truck_id: uuid.UUID,
        record_id: uuid.UUID,
    ) -> TruckTireRecord:
        record = self._repository.get_tire_by_id(
            record_id,
            truck_id,
            current_user.company_id,
        )
        if record is None:
            raise NotFoundError(
                code="TRUCK_TIRE_NOT_FOUND",
                message="Truck tire record not found.",
            )
        return record
