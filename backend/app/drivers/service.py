"""Driver business logic."""

import uuid

from sqlalchemy.orm import Session

from app.common.enums import OrderStatus, UserRole
from app.common.exceptions import NotFoundError, ValidationError
from app.common.tenant import ensure_same_company
from app.drivers.models import Driver
from app.drivers.repository import DriverRepository
from app.drivers.schemas import (
    DriverCreateRequest,
    DriverHomeResponse,
    DriverResponse,
    DriverUpdateRequest,
)
from app.drivers.validators import validate_driver_user
from app.notifications.service import NotificationService
from app.orders.repository import OrderRepository
from app.orders.schemas import OrderSummaryResponse
from app.trailers.repository import TrailerRepository
from app.trucks.repository import TruckRepository
from app.users.models import User
from app.users.repository import UserRepository

MAX_PAGE_SIZE = 100

NEXT_ACTIONS: dict[OrderStatus, str] = {
    OrderStatus.ASSIGNED: "Accept or reject this order",
    OrderStatus.ACCEPTED: "Navigate to pickup and confirm arrival",
    OrderStatus.LOADING: "Complete loading",
    OrderStatus.IN_TRANSIT: "Navigate to delivery",
    OrderStatus.DELIVERING: "Upload signed CMR and complete delivery",
    OrderStatus.COMPLETED: "No active tasks",
    OrderStatus.CANCELLED: "No active tasks",
    OrderStatus.READY: "Waiting for assignment",
    OrderStatus.DRAFT: "Waiting for assignment",
}

ACTIVE_ORDER_STATUSES = {
    OrderStatus.ASSIGNED,
    OrderStatus.ACCEPTED,
    OrderStatus.LOADING,
    OrderStatus.IN_TRANSIT,
    OrderStatus.DELIVERING,
}


class DriverService:
    """Driver profile workflows."""

    def __init__(self, db: Session) -> None:
        self._db = db
        self._repository = DriverRepository(db)
        self._users = UserRepository(db)
        self._orders = OrderRepository(db)
        self._trucks = TruckRepository(db)
        self._trailers = TrailerRepository(db)
        self._notifications = NotificationService(db)

    def list_drivers(
        self,
        current_user: User,
        *,
        page: int,
        page_size: int,
        active: bool | None,
        search: str | None,
    ) -> tuple[list[Driver], int]:
        """List drivers for the current company."""
        normalized_page = max(page, 1)
        normalized_page_size = min(max(page_size, 1), MAX_PAGE_SIZE)
        return self._repository.list_for_company(
            current_user.company_id,
            page=normalized_page,
            page_size=normalized_page_size,
            active=active,
            search=search,
        )

    def get_driver(self, current_user: User, driver_id: uuid.UUID) -> Driver:
        """Return a driver in the current company."""
        driver = self._repository.get_by_id_for_company(driver_id, current_user.company_id)
        if driver is None:
            raise NotFoundError(code="DRIVER_NOT_FOUND", message="Driver not found.")
        ensure_same_company(driver.company_id, current_user)
        return driver

    def create_driver(
        self,
        current_user: User,
        payload: DriverCreateRequest,
    ) -> Driver:
        """Create a driver profile for a user."""
        user = self._users.get_by_id_for_company(payload.user_id, current_user.company_id)
        if user is None:
            raise ValidationError(
                code="INVALID_DRIVER_USER",
                message="User not found in this company.",
            )
        validate_driver_user(user, current_user.company_id)

        existing_driver = self._repository.get_by_user_for_company(
            payload.user_id,
            current_user.company_id,
        )
        if existing_driver is not None:
            raise ValidationError(
                code="DRIVER_ALREADY_EXISTS",
                message="This user already has a driver profile.",
            )

        return self._repository.create(
            company_id=current_user.company_id,
            payload=payload,
            created_by=current_user.id,
        )

    def update_driver(
        self,
        current_user: User,
        driver_id: uuid.UUID,
        payload: DriverUpdateRequest,
    ) -> Driver:
        """Update a driver profile."""
        driver = self.get_driver(current_user, driver_id)
        return self._repository.update(driver, payload, current_user.id)

    def list_driver_orders(
        self,
        current_user: User,
        driver_id: uuid.UUID,
        *,
        page: int = 1,
        page_size: int = MAX_PAGE_SIZE,
    ) -> tuple[list[OrderSummaryResponse], int]:
        """Return orders assigned to a driver."""
        self.get_driver(current_user, driver_id)
        normalized_page = max(page, 1)
        normalized_page_size = min(max(page_size, 1), MAX_PAGE_SIZE)
        orders, total = self._orders.list_for_company(
            current_user.company_id,
            page=normalized_page,
            page_size=normalized_page_size,
            driver_id=driver_id,
        )
        summaries = [
            OrderSummaryResponse(
                id=order.id,
                order_number=order.order_number,
                status=OrderStatus(order.status),
                customer_id=order.customer_id,
                planned_pickup_date=order.planned_pickup_date,
                planned_delivery_date=order.planned_delivery_date,
                created_at=order.created_at,
            )
            for order in orders
        ]
        return summaries, total

    def get_my_driver(self, current_user: User) -> Driver:
        """Return the driver profile for the current user."""
        if current_user.role != UserRole.DRIVER:
            raise ValidationError(
                code="NOT_A_DRIVER",
                message="Current user is not a driver.",
            )
        driver = self._repository.get_by_user_for_company(
            current_user.id,
            current_user.company_id,
        )
        if driver is None:
            raise NotFoundError(code="DRIVER_NOT_FOUND", message="Driver profile not found.")
        return driver

    def list_my_orders(
        self,
        current_user: User,
        *,
        page: int,
        page_size: int,
    ) -> tuple[list[OrderSummaryResponse], int]:
        """Return orders assigned to the current driver."""
        driver = self.get_my_driver(current_user)
        return self.list_driver_orders(
            current_user,
            driver.id,
            page=page,
            page_size=page_size,
        )

    def get_home(self, current_user: User) -> DriverHomeResponse:
        """Return the driver home screen payload."""
        driver = self.get_my_driver(current_user)
        user_name = f"{current_user.first_name} {current_user.last_name}".strip()
        orders, _ = self._orders.list_for_company(
            current_user.company_id,
            page=1,
            page_size=MAX_PAGE_SIZE,
            driver_id=driver.id,
        )
        active_orders = [
            order
            for order in orders
            if OrderStatus(order.status) in ACTIVE_ORDER_STATUSES
        ]
        current_order: OrderSummaryResponse | None = None
        next_action = "No active orders"
        if active_orders:
            current = sorted(active_orders, key=lambda item: item.created_at)[0]
            current_order = OrderSummaryResponse(
                id=current.id,
                order_number=current.order_number,
                status=OrderStatus(current.status),
                customer_id=current.customer_id,
                planned_pickup_date=current.planned_pickup_date,
                planned_delivery_date=current.planned_delivery_date,
                created_at=current.created_at,
            )
            next_action = NEXT_ACTIONS.get(OrderStatus(current.status), "Review order details")

        truck_label: str | None = None
        trailer_label: str | None = None
        if active_orders and active_orders[0].assigned_truck_id is not None:
            truck = self._trucks.get_by_id_for_company(
                active_orders[0].assigned_truck_id,
                current_user.company_id,
            )
            if truck is not None:
                truck_label = truck.registration_number
        if active_orders and active_orders[0].assigned_trailer_id is not None:
            trailer = self._trailers.get_by_id_for_company(
                active_orders[0].assigned_trailer_id,
                current_user.company_id,
            )
            if trailer is not None:
                trailer_label = trailer.registration_number

        unread = self._notifications.count_unread(current_user)
        return DriverHomeResponse(
            driver=DriverResponse.model_validate(driver),
            user_name=user_name,
            truck_label=truck_label,
            trailer_label=trailer_label,
            current_order=current_order,
            next_action=next_action,
            unread_notifications=unread,
        )
