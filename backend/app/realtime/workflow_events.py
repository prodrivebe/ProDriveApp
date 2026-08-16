"""Workflow event type mapping for realtime publishing."""

from app.realtime.schemas import RealtimeEventType

WORKFLOW_REALTIME_EVENTS: dict[str, RealtimeEventType] = {
    "DRIVER_ACCEPTED": RealtimeEventType.ORDER_ACCEPTED,
    "DRIVER_REJECTED": RealtimeEventType.ORDER_REJECTED,
    "ARRIVED_PICKUP": RealtimeEventType.DRIVER_ARRIVED_PICKUP,
    "LOADING_STARTED": RealtimeEventType.LOADING_STARTED,
    "LOADING_COMPLETE": RealtimeEventType.LOADING_COMPLETED,
    "TRANSIT_STARTED": RealtimeEventType.TRANSIT_STARTED,
    "ARRIVED_DELIVERY": RealtimeEventType.ARRIVED_DELIVERY,
    "DELIVERY_FINISHED": RealtimeEventType.DELIVERY_STARTED,
    "DELIVERY_CMR_CONFIRMED": RealtimeEventType.ORDER_UPDATED,
    "DELIVERY_COMPLETE": RealtimeEventType.ORDER_COMPLETED,
}
