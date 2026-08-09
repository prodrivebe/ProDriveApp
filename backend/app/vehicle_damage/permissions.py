"""Vehicle damage authorization."""

from app.orders.permissions import require_order_actor, require_order_manager

require_damage_actor = require_order_actor
require_damage_manager = require_order_manager
