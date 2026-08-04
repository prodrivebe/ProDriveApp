"""User authorization helpers."""

from app.auth.permissions import require_roles
from app.common.enums import UserRole

require_user_admin = require_roles(UserRole.ADMIN)
