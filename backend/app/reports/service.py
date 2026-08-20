"""Report business logic."""

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.common.enums import OrderStatus
from app.drivers.repository import DriverRepository
from app.fleet.schemas import FleetEntitySummary, FleetOverviewResponse
from app.reports.repository import ReportRepository
from app.reports.schemas import (
    CustomerActivityItem,
    CustomersReportResponse,
    DriverActivityItem,
    DriversReportResponse,
    FleetReportResponse,
    KpiDashboardResponse,
    OrdersReportResponse,
)
from app.trailers.repository import TrailerRepository
from app.trucks.repository import TruckRepository
from app.users.models import User


class ReportService:
    """Reporting and KPI aggregation."""

    def __init__(self, db: Session) -> None:
        self._db = db
        self._reports = ReportRepository(db)
        self._drivers = DriverRepository(db)
        self._trucks = TruckRepository(db)
        self._trailers = TrailerRepository(db)

    def get_orders_report(self, current_user: User) -> OrdersReportResponse:
        """Return order activity summary."""
        by_status = self._reports.order_counts_by_status(current_user.company_id)
        total = sum(by_status.values())
        return OrdersReportResponse(
            total_orders=total,
            completed_orders=by_status.get(OrderStatus.COMPLETED, 0),
            cancelled_orders=by_status.get(OrderStatus.CANCELLED, 0),
            active_orders=total
            - by_status.get(OrderStatus.COMPLETED, 0)
            - by_status.get(OrderStatus.CANCELLED, 0),
            by_status=by_status,
        )

    def get_drivers_report(self, current_user: User) -> DriversReportResponse:
        """Return driver activity summary."""
        rows = self._reports.driver_activity(current_user.company_id)
        drivers = [
            DriverActivityItem(
                driver_id=row[0],
                driver_name=f"{row[1]} {row[2]}".strip(),
                assigned_orders=int(row[3] or 0),
                completed_orders=int(row[4] or 0),
                active_orders=int(row[5] or 0),
            )
            for row in rows
        ]
        return DriversReportResponse(total_drivers=len(drivers), drivers=drivers)

    def get_customers_report(self, current_user: User) -> CustomersReportResponse:
        """Return customer activity summary."""
        rows = self._reports.customer_activity(current_user.company_id)
        customers = [
            CustomerActivityItem(
                customer_id=row[0],
                company_name=row[1],
                total_orders=int(row[2] or 0),
                completed_orders=int(row[3] or 0),
            )
            for row in rows
        ]
        return CustomersReportResponse(
            total_customers=self._reports.count_customers(current_user.company_id),
            customers=customers,
        )

    def get_fleet_report(self, current_user: User) -> FleetReportResponse:
        """Return fleet utilization summary."""
        driver_total, driver_active = self._drivers.count_for_company(current_user.company_id)
        truck_total, truck_active = self._trucks.count_for_company(current_user.company_id)
        trailer_total, trailer_active = self._trailers.count_for_company(
            current_user.company_id
        )
        assigned_drivers, assigned_trucks, assigned_trailers = (
            self._reports.count_assigned_fleet(current_user.company_id)
        )
        return FleetReportResponse(
            drivers=FleetEntitySummary(total=driver_total, active=driver_active),
            trucks=FleetEntitySummary(total=truck_total, active=truck_active),
            trailers=FleetEntitySummary(total=trailer_total, active=trailer_active),
            assigned_drivers=assigned_drivers,
            assigned_trucks=assigned_trucks,
            assigned_trailers=assigned_trailers,
        )

    def get_kpi_dashboard(self, current_user: User) -> KpiDashboardResponse:
        """Return high-level KPI dashboard."""
        orders_report = self.get_orders_report(current_user)
        fleet_report = self.get_fleet_report(current_user)
        return KpiDashboardResponse(
            total_orders=orders_report.total_orders,
            completed_orders=orders_report.completed_orders,
            active_orders=orders_report.active_orders,
            total_customers=self._reports.count_customers(current_user.company_id),
            total_drivers=fleet_report.drivers.total,
            active_drivers=fleet_report.drivers.active,
            fleet=FleetOverviewResponse(
                drivers=fleet_report.drivers,
                trucks=fleet_report.trucks,
                trailers=fleet_report.trailers,
            ),
            generated_at=datetime.now(tz=UTC),
        )
