"""Report API routes."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.responses import SuccessResponse, success_response
from app.database.session import get_db
from app.reports.permissions import require_report_reader
from app.reports.schemas import (
    CustomersReportResponse,
    DriversReportResponse,
    FleetReportResponse,
    KpiDashboardResponse,
    OrdersReportResponse,
)
from app.reports.service import ReportService
from app.users.models import User

router = APIRouter(prefix="/reports", tags=["Reports"])


def get_report_service(db: Session = Depends(get_db)) -> ReportService:
    """Provide a report service instance."""
    return ReportService(db)


@router.get("/orders", response_model=SuccessResponse[OrdersReportResponse])
def get_orders_report(
    current_user: User = Depends(require_report_reader),
    report_service: ReportService = Depends(get_report_service),
) -> SuccessResponse[OrdersReportResponse]:
    """Return order activity report."""
    return success_response(report_service.get_orders_report(current_user))


@router.get("/drivers", response_model=SuccessResponse[DriversReportResponse])
def get_drivers_report(
    current_user: User = Depends(require_report_reader),
    report_service: ReportService = Depends(get_report_service),
) -> SuccessResponse[DriversReportResponse]:
    """Return driver activity report."""
    return success_response(report_service.get_drivers_report(current_user))


@router.get("/customers", response_model=SuccessResponse[CustomersReportResponse])
def get_customers_report(
    current_user: User = Depends(require_report_reader),
    report_service: ReportService = Depends(get_report_service),
) -> SuccessResponse[CustomersReportResponse]:
    """Return customer activity report."""
    return success_response(report_service.get_customers_report(current_user))


@router.get("/fleet", response_model=SuccessResponse[FleetReportResponse])
def get_fleet_report(
    current_user: User = Depends(require_report_reader),
    report_service: ReportService = Depends(get_report_service),
) -> SuccessResponse[FleetReportResponse]:
    """Return fleet utilization report."""
    return success_response(report_service.get_fleet_report(current_user))


@router.get("/kpi", response_model=SuccessResponse[KpiDashboardResponse])
def get_kpi_dashboard(
    current_user: User = Depends(require_report_reader),
    report_service: ReportService = Depends(get_report_service),
) -> SuccessResponse[KpiDashboardResponse]:
    """Return KPI dashboard summary."""
    return success_response(report_service.get_kpi_dashboard(current_user))
