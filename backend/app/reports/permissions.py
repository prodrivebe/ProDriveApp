"""Report authorization helpers."""

from app.auth.permissions import require_roles
from app.common.enums import UserRole

require_report_reader = require_roles(UserRole.ADMIN, UserRole.DISPATCHER)
