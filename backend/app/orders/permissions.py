"""Order authorization helpers."""

from app.auth.permissions import require_roles
from app.common.enums import UserRole

require_order_manager = require_roles(UserRole.ADMIN, UserRole.DISPATCHER)
require_order_actor = require_roles(UserRole.ADMIN, UserRole.DISPATCHER, UserRole.DRIVER)
