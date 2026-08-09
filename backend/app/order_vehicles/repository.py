"""Order vehicle persistence layer."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.orders.models import OrderVehicle
from app.order_vehicles.schemas import OrderVehicleCreateRequest, OrderVehicleUpdateRequest


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
