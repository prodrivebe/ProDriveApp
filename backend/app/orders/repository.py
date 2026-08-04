"""Order persistence layer."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.common.enums import OrderStatus
from app.orders.models import Order, OrderStop, OrderTimelineEntry, OrderVehicle
from app.orders.schemas import (
    OrderCreateRequest,
    OrderStopCreateRequest,
    OrderStopUpdateRequest,
    OrderUpdateRequest,
    OrderVehicleCreateRequest,
    OrderVehicleUpdateRequest,
)


class OrderRepository:
    """Repository for order records."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_id_for_company(
        self,
        order_id: uuid.UUID,
        company_id: uuid.UUID,
        *,
        with_details: bool = False,
    ) -> Order | None:
        """Return an order scoped to a company."""
        statement = select(Order).where(
            Order.id == order_id,
            Order.company_id == company_id,
            Order.deleted_at.is_(None),
        )
        if with_details:
            statement = statement.options(
                selectinload(Order.stops),
                selectinload(Order.vehicles),
            )
        return self._db.scalar(statement)

    def list_for_company(
        self,
        company_id: uuid.UUID,
        *,
        page: int,
        page_size: int,
        status: OrderStatus | None = None,
        customer_id: uuid.UUID | None = None,
        driver_id: uuid.UUID | None = None,
        search: str | None = None,
    ) -> tuple[list[Order], int]:
        """Return paginated orders for a company."""
        filters = [Order.company_id == company_id, Order.deleted_at.is_(None)]
        if status is not None:
            filters.append(Order.status == status)
        if customer_id is not None:
            filters.append(Order.customer_id == customer_id)
        if driver_id is not None:
            filters.append(Order.assigned_driver_id == driver_id)
        if search:
            pattern = f"%{search.strip()}%"
            filters.append(
                or_(
                    Order.order_number.ilike(pattern),
                    Order.notes.ilike(pattern),
                )
            )

        total = int(
            self._db.scalar(select(func.count()).select_from(Order).where(*filters)) or 0
        )
        statement = (
            select(Order)
            .where(*filters)
            .order_by(Order.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(self._db.scalars(statement).all()), total

    def count_for_company(self, company_id: uuid.UUID) -> int:
        """Return the number of orders for a company."""
        return int(
            self._db.scalar(
                select(func.count())
                .select_from(Order)
                .where(Order.company_id == company_id, Order.deleted_at.is_(None))
            )
            or 0
        )

    def create(
        self,
        *,
        company_id: uuid.UUID,
        customer_id: uuid.UUID,
        order_number: str,
        payload: OrderCreateRequest,
        created_by: uuid.UUID,
    ) -> Order:
        """Create an order record."""
        order = Order(
            company_id=company_id,
            customer_id=customer_id,
            order_number=order_number,
            status=OrderStatus.DRAFT,
            planned_pickup_date=payload.planned_pickup_date,
            planned_delivery_date=payload.planned_delivery_date,
            notes=payload.notes,
            created_by=created_by,
            updated_by=created_by,
        )
        self._db.add(order)
        self._db.commit()
        self._db.refresh(order)
        return order

    def update(
        self,
        order: Order,
        payload: OrderUpdateRequest,
        updated_by: uuid.UUID,
    ) -> Order:
        """Update an order record."""
        order.customer_id = payload.customer_id
        order.planned_pickup_date = payload.planned_pickup_date
        order.planned_delivery_date = payload.planned_delivery_date
        order.notes = payload.notes
        if payload.status is not None:
            order.status = payload.status
        order.updated_by = updated_by
        self._db.add(order)
        self._db.commit()
        self._db.refresh(order)
        return order

    def update_status(
        self,
        order: Order,
        status: OrderStatus,
        updated_by: uuid.UUID,
        *,
        assigned_driver_id: uuid.UUID | None = None,
        assigned_truck_id: uuid.UUID | None = None,
        assigned_trailer_id: uuid.UUID | None = None,
        clear_assignment: bool = False,
    ) -> Order:
        """Update order status and optional assignment fields."""
        order.status = status
        order.updated_by = updated_by
        if clear_assignment:
            order.assigned_driver_id = None
            order.assigned_truck_id = None
            order.assigned_trailer_id = None
        else:
            if assigned_driver_id is not None:
                order.assigned_driver_id = assigned_driver_id
            if assigned_truck_id is not None:
                order.assigned_truck_id = assigned_truck_id
            if assigned_trailer_id is not None:
                order.assigned_trailer_id = assigned_trailer_id
        self._db.add(order)
        self._db.commit()
        self._db.refresh(order)
        return order

    def soft_delete(self, order: Order, deleted_by: uuid.UUID) -> Order:
        """Soft delete an order record."""
        order.deleted_at = datetime.now(tz=UTC)
        order.updated_by = deleted_by
        self._db.add(order)
        self._db.commit()
        self._db.refresh(order)
        return order


class OrderStopRepository:
    """Repository for order stop records."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_id_for_company(
        self,
        stop_id: uuid.UUID,
        company_id: uuid.UUID,
    ) -> OrderStop | None:
        """Return a stop scoped to a company."""
        statement = select(OrderStop).where(
            OrderStop.id == stop_id,
            OrderStop.company_id == company_id,
            OrderStop.deleted_at.is_(None),
        )
        return self._db.scalar(statement)

    def list_for_order(self, order_id: uuid.UUID, company_id: uuid.UUID) -> list[OrderStop]:
        """Return stops for an order."""
        statement = (
            select(OrderStop)
            .where(
                OrderStop.order_id == order_id,
                OrderStop.company_id == company_id,
                OrderStop.deleted_at.is_(None),
            )
            .order_by(OrderStop.sequence.asc())
        )
        return list(self._db.scalars(statement).all())

    def create(
        self,
        *,
        company_id: uuid.UUID,
        order_id: uuid.UUID,
        payload: OrderStopCreateRequest,
        created_by: uuid.UUID,
    ) -> OrderStop:
        """Create an order stop."""
        stop = OrderStop(
            company_id=company_id,
            order_id=order_id,
            stop_type=payload.stop_type,
            sequence=payload.sequence,
            company_name=payload.company_name,
            contact_name=payload.contact_name,
            phone=payload.phone,
            address=payload.address,
            city=payload.city,
            postal_code=payload.postal_code,
            country=payload.country,
            latitude=payload.latitude,
            longitude=payload.longitude,
            created_by=created_by,
            updated_by=created_by,
        )
        self._db.add(stop)
        self._db.commit()
        self._db.refresh(stop)
        return stop

    def update(
        self,
        stop: OrderStop,
        payload: OrderStopUpdateRequest,
        updated_by: uuid.UUID,
    ) -> OrderStop:
        """Update an order stop."""
        stop.stop_type = payload.stop_type
        stop.sequence = payload.sequence
        stop.company_name = payload.company_name
        stop.contact_name = payload.contact_name
        stop.phone = payload.phone
        stop.address = payload.address
        stop.city = payload.city
        stop.postal_code = payload.postal_code
        stop.country = payload.country
        stop.latitude = payload.latitude
        stop.longitude = payload.longitude
        stop.updated_by = updated_by
        self._db.add(stop)
        self._db.commit()
        self._db.refresh(stop)
        return stop

    def soft_delete(self, stop: OrderStop, deleted_by: uuid.UUID) -> OrderStop:
        """Soft delete an order stop."""
        stop.deleted_at = datetime.now(tz=UTC)
        stop.updated_by = deleted_by
        self._db.add(stop)
        self._db.commit()
        self._db.refresh(stop)
        return stop


class OrderVehicleRepository:
    """Repository for order vehicle records."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_id_for_company(
        self,
        vehicle_id: uuid.UUID,
        company_id: uuid.UUID,
    ) -> OrderVehicle | None:
        """Return a vehicle scoped to a company."""
        statement = select(OrderVehicle).where(
            OrderVehicle.id == vehicle_id,
            OrderVehicle.company_id == company_id,
            OrderVehicle.deleted_at.is_(None),
        )
        return self._db.scalar(statement)

    def list_for_order(self, order_id: uuid.UUID, company_id: uuid.UUID) -> list[OrderVehicle]:
        """Return vehicles for an order."""
        statement = (
            select(OrderVehicle)
            .where(
                OrderVehicle.order_id == order_id,
                OrderVehicle.company_id == company_id,
                OrderVehicle.deleted_at.is_(None),
            )
            .order_by(OrderVehicle.created_at.asc())
        )
        return list(self._db.scalars(statement).all())

    def create(
        self,
        *,
        company_id: uuid.UUID,
        order_id: uuid.UUID,
        payload: OrderVehicleCreateRequest,
        created_by: uuid.UUID,
        vin: str | None = None,
    ) -> OrderVehicle:
        """Create an order vehicle."""
        vehicle = OrderVehicle(
            company_id=company_id,
            order_id=order_id,
            pickup_stop_id=payload.pickup_stop_id,
            delivery_stop_id=payload.delivery_stop_id,
            vin=vin,
            make=payload.make,
            model=payload.model,
            generation=payload.generation,
            body_type=payload.body_type,
            color=payload.color,
            year=payload.year,
            fuel_type=payload.fuel_type,
            transmission=payload.transmission,
            running=payload.running,
            estimated_weight=payload.estimated_weight,
            estimated_height=payload.estimated_height,
            notes=payload.notes,
            created_by=created_by,
            updated_by=created_by,
        )
        self._db.add(vehicle)
        self._db.commit()
        self._db.refresh(vehicle)
        return vehicle

    def update(
        self,
        vehicle: OrderVehicle,
        payload: OrderVehicleUpdateRequest,
        updated_by: uuid.UUID,
        *,
        vin: str | None = None,
    ) -> OrderVehicle:
        """Update an order vehicle."""
        vehicle.pickup_stop_id = payload.pickup_stop_id
        vehicle.delivery_stop_id = payload.delivery_stop_id
        if vin is not None:
            vehicle.vin = vin
        vehicle.make = payload.make
        vehicle.model = payload.model
        vehicle.generation = payload.generation
        vehicle.body_type = payload.body_type
        vehicle.color = payload.color
        vehicle.year = payload.year
        vehicle.fuel_type = payload.fuel_type
        vehicle.transmission = payload.transmission
        vehicle.running = payload.running
        vehicle.estimated_weight = payload.estimated_weight
        vehicle.estimated_height = payload.estimated_height
        vehicle.notes = payload.notes
        vehicle.updated_by = updated_by
        self._db.add(vehicle)
        self._db.commit()
        self._db.refresh(vehicle)
        return vehicle

    def update_vin(
        self,
        vehicle: OrderVehicle,
        vin: str,
        updated_by: uuid.UUID,
    ) -> OrderVehicle:
        """Update only the vehicle VIN."""
        vehicle.vin = vin
        vehicle.updated_by = updated_by
        self._db.add(vehicle)
        self._db.commit()
        self._db.refresh(vehicle)
        return vehicle

    def soft_delete(self, vehicle: OrderVehicle, deleted_by: uuid.UUID) -> OrderVehicle:
        """Soft delete an order vehicle."""
        vehicle.deleted_at = datetime.now(tz=UTC)
        vehicle.updated_by = deleted_by
        self._db.add(vehicle)
        self._db.commit()
        self._db.refresh(vehicle)
        return vehicle


class OrderTimelineRepository:
    """Repository for order timeline records."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def list_for_order(self, order_id: uuid.UUID, company_id: uuid.UUID) -> list[OrderTimelineEntry]:
        """Return timeline entries for an order."""
        statement = (
            select(OrderTimelineEntry)
            .where(
                OrderTimelineEntry.order_id == order_id,
                OrderTimelineEntry.company_id == company_id,
            )
            .order_by(OrderTimelineEntry.created_at.asc())
        )
        return list(self._db.scalars(statement).all())

    def create(
        self,
        *,
        company_id: uuid.UUID,
        order_id: uuid.UUID,
        event_type: str,
        description: str,
        created_by: uuid.UUID | None,
    ) -> OrderTimelineEntry:
        """Create a timeline entry."""
        entry = OrderTimelineEntry(
            company_id=company_id,
            order_id=order_id,
            event_type=event_type,
            description=description,
            created_by=created_by,
            created_at=datetime.now(tz=UTC),
        )
        self._db.add(entry)
        self._db.commit()
        self._db.refresh(entry)
        return entry
