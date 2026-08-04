"""Report API schemas."""

import uuid
from datetime import date, datetime

from datetime import datetime

from pydantic import BaseModel

from app.fleet.schemas import FleetEntitySummary


class OrdersReportResponse(BaseModel):
    """Order activity summary."""

    total_orders: int
    completed_orders: int
    cancelled_orders: int
    active_orders: int
    by_status: dict[str, int]


class DriverActivityItem(BaseModel):
    """Driver activity summary row."""

    driver_id: uuid.UUID
    driver_name: str
    assigned_orders: int
    completed_orders: int
    active_orders: int


class DriversReportResponse(BaseModel):
    """Driver activity report."""

    total_drivers: int
    drivers: list[DriverActivityItem]


class CustomerActivityItem(BaseModel):
    """Customer activity summary row."""

    customer_id: uuid.UUID
    company_name: str
    total_orders: int
    completed_orders: int


class CustomersReportResponse(BaseModel):
    """Customer activity report."""

    total_customers: int
    customers: list[CustomerActivityItem]


class FleetReportResponse(BaseModel):
    """Fleet utilization report."""

    drivers: FleetEntitySummary
    trucks: FleetEntitySummary
    trailers: FleetEntitySummary
    assigned_drivers: int
    assigned_trucks: int
    assigned_trailers: int


class KpiDashboardResponse(BaseModel):
    """High-level KPI dashboard."""

    total_orders: int
    completed_orders: int
    active_orders: int
    total_customers: int
    total_drivers: int
    active_drivers: int
    fleet: FleetEntitySummary
    generated_at: datetime
