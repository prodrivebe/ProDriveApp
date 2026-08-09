"""Shared vehicle execution access helpers."""

import uuid

from app.common.enums import UserRole
from app.common.exceptions import AuthorizationError, NotFoundError
from app.drivers.models import Driver
from app.drivers.repository import DriverRepository
from app.orders.models import Order, OrderVehicle
from app.orders.repository import OrderRepository, OrderVehicleRepository
from app.orders.validators import ensure_order_view_access, ensure_workflow_actor
from app.users.models import User


def get_order_for_company(
    orders: OrderRepository,
    order_id: uuid.UUID,
    company_id: uuid.UUID,
) -> Order:
    """Load an order scoped to a company or raise 404."""
    order = orders.get_by_id_for_company(order_id, company_id)
    if order is None:
        raise NotFoundError(code="ORDER_NOT_FOUND", message="Order not found.")
    return order


def get_vehicle_for_order(
    vehicles: OrderVehicleRepository,
    *,
    order_id: uuid.UUID,
    vehicle_id: uuid.UUID,
    company_id: uuid.UUID,
) -> OrderVehicle:
    """Load a vehicle belonging to an order."""
    vehicle = vehicles.get_by_id_for_company(vehicle_id, company_id)
    if vehicle is None or vehicle.order_id != order_id:
        raise NotFoundError(code="VEHICLE_NOT_FOUND", message="Vehicle not found.")
    return vehicle


def ensure_execution_access(
    current_user: User,
    order: Order,
    drivers: DriverRepository,
    *,
    require_assigned_driver: bool = False,
) -> Driver | None:
    """Ensure the user can perform vehicle execution actions on an order."""
    driver: Driver | None = None
    if order.assigned_driver_id is not None:
        driver = drivers.get_by_id_for_company(order.assigned_driver_id, order.company_id)
    if require_assigned_driver and current_user.role == UserRole.DRIVER:
        ensure_workflow_actor(current_user, order, driver)
    else:
        ensure_order_view_access(current_user, order, driver)
        if current_user.role == UserRole.DRIVER:
            ensure_workflow_actor(current_user, order, driver)
    return driver
