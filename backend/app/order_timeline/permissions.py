"""Order timeline authorization helpers."""

from app.orders.permissions import require_order_actor

__all__ = ["require_order_actor"]
