"""Truck operational record API routes."""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.responses import SuccessResponse, success_response
from app.database.session import get_db
from app.fleet.permissions import require_fleet_manager
from app.trucks.operational_schemas import (
    TruckInspectionRecordCreateRequest,
    TruckInspectionRecordResponse,
    TruckInspectionRecordUpdateRequest,
    TruckMaintenanceRecordCreateRequest,
    TruckMaintenanceRecordResponse,
    TruckMaintenanceRecordUpdateRequest,
    TruckTireRecordCreateRequest,
    TruckTireRecordResponse,
    TruckTireRecordUpdateRequest,
)
from app.trucks.operational_service import TruckOperationalService
from app.users.models import User

router = APIRouter(prefix="/trucks/{truck_id}", tags=["Truck Operations"])


def get_operational_service(db: Session = Depends(get_db)) -> TruckOperationalService:
    """Provide a truck operational service instance."""
    return TruckOperationalService(db)


@router.get("/maintenance", response_model=SuccessResponse[list[TruckMaintenanceRecordResponse]])
def list_truck_maintenance(
    truck_id: uuid.UUID,
    current_user: User = Depends(require_fleet_manager),
    service: TruckOperationalService = Depends(get_operational_service),
) -> SuccessResponse[list[TruckMaintenanceRecordResponse]]:
    """List maintenance records for a truck."""
    records = service.list_maintenance(current_user, truck_id)
    data = [TruckMaintenanceRecordResponse.model_validate(record) for record in records]
    return success_response(data)


@router.post(
    "/maintenance",
    response_model=SuccessResponse[TruckMaintenanceRecordResponse],
    status_code=201,
)
def create_truck_maintenance(
    truck_id: uuid.UUID,
    payload: TruckMaintenanceRecordCreateRequest,
    current_user: User = Depends(require_fleet_manager),
    service: TruckOperationalService = Depends(get_operational_service),
) -> SuccessResponse[TruckMaintenanceRecordResponse]:
    """Create a maintenance record for a truck."""
    record = service.create_maintenance(current_user, truck_id, payload)
    return success_response(TruckMaintenanceRecordResponse.model_validate(record))


@router.put(
    "/maintenance/{record_id}",
    response_model=SuccessResponse[TruckMaintenanceRecordResponse],
)
def update_truck_maintenance(
    truck_id: uuid.UUID,
    record_id: uuid.UUID,
    payload: TruckMaintenanceRecordUpdateRequest,
    current_user: User = Depends(require_fleet_manager),
    service: TruckOperationalService = Depends(get_operational_service),
) -> SuccessResponse[TruckMaintenanceRecordResponse]:
    """Update a maintenance record."""
    record = service.update_maintenance(current_user, truck_id, record_id, payload)
    return success_response(TruckMaintenanceRecordResponse.model_validate(record))


@router.delete("/maintenance/{record_id}", response_model=SuccessResponse[dict[str, str]])
def delete_truck_maintenance(
    truck_id: uuid.UUID,
    record_id: uuid.UUID,
    current_user: User = Depends(require_fleet_manager),
    service: TruckOperationalService = Depends(get_operational_service),
) -> SuccessResponse[dict[str, str]]:
    """Soft delete a maintenance record."""
    service.delete_maintenance(current_user, truck_id, record_id)
    return success_response({"message": "Truck maintenance record deleted successfully."})


@router.get("/inspections", response_model=SuccessResponse[list[TruckInspectionRecordResponse]])
def list_truck_inspections(
    truck_id: uuid.UUID,
    current_user: User = Depends(require_fleet_manager),
    service: TruckOperationalService = Depends(get_operational_service),
) -> SuccessResponse[list[TruckInspectionRecordResponse]]:
    """List inspection records for a truck."""
    records = service.list_inspections(current_user, truck_id)
    data = [TruckInspectionRecordResponse.model_validate(record) for record in records]
    return success_response(data)


@router.post(
    "/inspections",
    response_model=SuccessResponse[TruckInspectionRecordResponse],
    status_code=201,
)
def create_truck_inspection(
    truck_id: uuid.UUID,
    payload: TruckInspectionRecordCreateRequest,
    current_user: User = Depends(require_fleet_manager),
    service: TruckOperationalService = Depends(get_operational_service),
) -> SuccessResponse[TruckInspectionRecordResponse]:
    """Create an inspection record for a truck."""
    record = service.create_inspection(current_user, truck_id, payload)
    return success_response(TruckInspectionRecordResponse.model_validate(record))


@router.put(
    "/inspections/{record_id}",
    response_model=SuccessResponse[TruckInspectionRecordResponse],
)
def update_truck_inspection(
    truck_id: uuid.UUID,
    record_id: uuid.UUID,
    payload: TruckInspectionRecordUpdateRequest,
    current_user: User = Depends(require_fleet_manager),
    service: TruckOperationalService = Depends(get_operational_service),
) -> SuccessResponse[TruckInspectionRecordResponse]:
    """Update an inspection record."""
    record = service.update_inspection(current_user, truck_id, record_id, payload)
    return success_response(TruckInspectionRecordResponse.model_validate(record))


@router.delete("/inspections/{record_id}", response_model=SuccessResponse[dict[str, str]])
def delete_truck_inspection(
    truck_id: uuid.UUID,
    record_id: uuid.UUID,
    current_user: User = Depends(require_fleet_manager),
    service: TruckOperationalService = Depends(get_operational_service),
) -> SuccessResponse[dict[str, str]]:
    """Soft delete an inspection record."""
    service.delete_inspection(current_user, truck_id, record_id)
    return success_response({"message": "Truck inspection record deleted successfully."})


@router.get("/tires", response_model=SuccessResponse[list[TruckTireRecordResponse]])
def list_truck_tires(
    truck_id: uuid.UUID,
    current_user: User = Depends(require_fleet_manager),
    service: TruckOperationalService = Depends(get_operational_service),
) -> SuccessResponse[list[TruckTireRecordResponse]]:
    """List tire records for a truck."""
    records = service.list_tires(current_user, truck_id)
    data = [TruckTireRecordResponse.model_validate(record) for record in records]
    return success_response(data)


@router.post(
    "/tires",
    response_model=SuccessResponse[TruckTireRecordResponse],
    status_code=201,
)
def create_truck_tire(
    truck_id: uuid.UUID,
    payload: TruckTireRecordCreateRequest,
    current_user: User = Depends(require_fleet_manager),
    service: TruckOperationalService = Depends(get_operational_service),
) -> SuccessResponse[TruckTireRecordResponse]:
    """Create a tire record for a truck."""
    record = service.create_tire(current_user, truck_id, payload)
    return success_response(TruckTireRecordResponse.model_validate(record))


@router.put(
    "/tires/{record_id}",
    response_model=SuccessResponse[TruckTireRecordResponse],
)
def update_truck_tire(
    truck_id: uuid.UUID,
    record_id: uuid.UUID,
    payload: TruckTireRecordUpdateRequest,
    current_user: User = Depends(require_fleet_manager),
    service: TruckOperationalService = Depends(get_operational_service),
) -> SuccessResponse[TruckTireRecordResponse]:
    """Update a tire record."""
    record = service.update_tire(current_user, truck_id, record_id, payload)
    return success_response(TruckTireRecordResponse.model_validate(record))


@router.delete("/tires/{record_id}", response_model=SuccessResponse[dict[str, str]])
def delete_truck_tire(
    truck_id: uuid.UUID,
    record_id: uuid.UUID,
    current_user: User = Depends(require_fleet_manager),
    service: TruckOperationalService = Depends(get_operational_service),
) -> SuccessResponse[dict[str, str]]:
    """Soft delete a tire record."""
    service.delete_tire(current_user, truck_id, record_id)
    return success_response({"message": "Truck tire record deleted successfully."})
