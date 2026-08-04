"""Fleet overview API routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.responses import SuccessResponse, success_response
from app.database.session import get_db
from app.fleet.permissions import require_fleet_manager
from app.fleet.schemas import FleetOverviewResponse
from app.fleet.service import FleetOverviewService
from app.users.models import User

router = APIRouter(prefix="/fleet", tags=["Fleet"])


def get_fleet_overview_service(db: Session = Depends(get_db)) -> FleetOverviewService:
    """Provide a fleet overview service instance."""
    return FleetOverviewService(db)


@router.get("/overview", response_model=SuccessResponse[FleetOverviewResponse])
def get_fleet_overview(
    current_user: User = Depends(require_fleet_manager),
    fleet_service: FleetOverviewService = Depends(get_fleet_overview_service),
) -> SuccessResponse[FleetOverviewResponse]:
    """Return fleet overview for the current company."""
    overview = fleet_service.get_overview(current_user)
    return success_response(overview)
