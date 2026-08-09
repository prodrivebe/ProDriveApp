"""Driver workflow API schemas."""

import uuid

from pydantic import BaseModel, ConfigDict

from app.common.enums import OrderStatus
from app.order_stops.schemas import OrderStopResponse
from app.order_vehicles.schemas import OrderVehicleResponse
from app.orders.schemas import OrderResponse


class DriverCurrentOrderResponse(BaseModel):
    """Payload for the driver home screen current-order endpoint."""

    model_config = ConfigDict(from_attributes=True)

    order: OrderResponse | None = None
    current_stop: OrderStopResponse | None = None
    remaining_stops: list[OrderStopResponse] = []
    vehicles: list[OrderVehicleResponse] = []
    next_required_action: str = "No active orders"
    workflow_status: OrderStatus | None = None
