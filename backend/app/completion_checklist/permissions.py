"""Completion checklist authorization."""

from app.orders.permissions import require_order_actor, require_order_manager

require_checklist_actor = require_order_actor
require_checklist_manager = require_order_manager
