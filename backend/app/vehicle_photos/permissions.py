"""Vehicle photo authorization."""

from app.orders.permissions import require_order_actor, require_order_manager

require_photo_actor = require_order_actor
require_photo_manager = require_order_manager
