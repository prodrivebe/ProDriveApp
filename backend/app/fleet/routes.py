"""Fleet API routes."""

import uuid

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.common.responses import SuccessResponse, success_response
from app.database.session import get_db
from app.drivers.permissions import require_driver
from app.fleet.assignment_service import FleetAssignmentService
from app.fleet.permissions import require_fleet_manager
from app.fleet.schemas import (
    FleetAssignmentCreateRequest,
    FleetAssignmentResponse,
    FleetOverviewResponse,
)
from app.fleet.service import FleetOverviewService
from app.users.models import User

router = APIRouter(prefix="/fleet", tags=["Fleet"])


def get_client_ip(request: Request) -> str | None:
    """Extract the client IP address from the request."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip()
    if request.client is not None:
        return request.client.host
    return None


def get_fleet_overview_service(db: Session = Depends(get_db)) -> FleetOverviewService:
    """Provide a fleet overview service instance."""
    return FleetOverviewService(db)


def get_fleet_assignment_service(
    db: Session = Depends(get_db),
) -> FleetAssignmentService:
    """Provide a fleet assignment service instance."""
    return FleetAssignmentService(db)


@router.get("/overview", response_model=SuccessResponse[FleetOverviewResponse])
def get_fleet_overview(
    current_user: User = Depends(require_fleet_manager),
    fleet_service: FleetOverviewService = Depends(get_fleet_overview_service),
) -> SuccessResponse[FleetOverviewResponse]:
    """Return fleet overview for the current company."""
    overview = fleet_service.get_overview(current_user)
    return success_response(overview)


@router.get(
    "/assignments",
    response_model=SuccessResponse[list[FleetAssignmentResponse]],
)
def list_fleet_assignments(
    active_only: bool = Query(default=False),
    current_user: User = Depends(require_fleet_manager),
    assignment_service: FleetAssignmentService = Depends(get_fleet_assignment_service),
) -> SuccessResponse[list[FleetAssignmentResponse]]:
    """List fleet assignments for the current company."""
    assignments = assignment_service.list_assignments(
        current_user,
        active_only=active_only,
    )
    data = [FleetAssignmentResponse.model_validate(item) for item in assignments]
    return success_response(data)


@router.get("/assignments/me", response_model=SuccessResponse[FleetAssignmentResponse])
def get_my_fleet_assignment(
    current_user: User = Depends(require_driver),
    assignment_service: FleetAssignmentService = Depends(get_fleet_assignment_service),
) -> SuccessResponse[FleetAssignmentResponse]:
    """Return the active fleet assignment for the current driver."""
    assignment = assignment_service.get_my_assignment(current_user)
    return success_response(FleetAssignmentResponse.model_validate(assignment))


@router.post(
    "/assignments",
    response_model=SuccessResponse[FleetAssignmentResponse],
    status_code=201,
)
def create_fleet_assignment(
    payload: FleetAssignmentCreateRequest,
    request: Request,
    current_user: User = Depends(require_fleet_manager),
    assignment_service: FleetAssignmentService = Depends(get_fleet_assignment_service),
) -> SuccessResponse[FleetAssignmentResponse]:
    """Create a standing fleet assignment."""
    assignment = assignment_service.create_assignment(
        current_user,
        payload,
        get_client_ip(request),
    )
    return success_response(FleetAssignmentResponse.model_validate(assignment))


@router.delete(
    "/assignments/{assignment_id}",
    response_model=SuccessResponse[FleetAssignmentResponse],
)
def remove_fleet_assignment(
    assignment_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(require_fleet_manager),
    assignment_service: FleetAssignmentService = Depends(get_fleet_assignment_service),
) -> SuccessResponse[FleetAssignmentResponse]:
    """Deactivate a fleet assignment."""
    assignment = assignment_service.remove_assignment(
        current_user,
        assignment_id,
        get_client_ip(request),
    )
    return success_response(FleetAssignmentResponse.model_validate(assignment))
