"""Company authorization helpers."""

from app.auth.permissions import require_roles
from app.common.enums import UserRole

require_company_admin = require_roles(UserRole.ADMIN)
require_company_reader = require_roles(
    UserRole.ADMIN,
    UserRole.DISPATCHER,
)
