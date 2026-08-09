"""Order document authorization."""

from app.orders.permissions import require_order_actor, require_order_manager

require_document_actor = require_order_actor
require_document_manager = require_order_manager
