"""Fleet overview business logic."""

from sqlalchemy.orm import Session

from app.drivers.repository import DriverRepository
from app.fleet.schemas import FleetEntitySummary, FleetOverviewResponse
from app.trailers.repository import TrailerRepository
from app.trucks.repository import TruckRepository
from app.users.models import User


class FleetOverviewService:
    """Aggregate fleet statistics for a company."""

    def __init__(self, db: Session) -> None:
        self._drivers = DriverRepository(db)
        self._trucks = TruckRepository(db)
        self._trailers = TrailerRepository(db)

    def get_overview(self, current_user: User) -> FleetOverviewResponse:
        """Return fleet overview for the current company."""
        driver_total, driver_active = self._drivers.count_for_company(current_user.company_id)
        truck_total, truck_active = self._trucks.count_for_company(current_user.company_id)
        trailer_total, trailer_active = self._trailers.count_for_company(
            current_user.company_id
        )
        return FleetOverviewResponse(
            drivers=FleetEntitySummary(total=driver_total, active=driver_active),
            trucks=FleetEntitySummary(total=truck_total, active=truck_active),
            trailers=FleetEntitySummary(total=trailer_total, active=trailer_active),
        )
