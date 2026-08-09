"""VIN verification authorization."""

from app.orders.permissions import require_order_actor

require_vin_actor = require_order_actor
