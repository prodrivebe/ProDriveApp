"""Driver authorization helpers."""

from app.auth.permissions import require_roles
from app.common.enums import UserRole

require_driver = require_roles(UserRole.DRIVER)
