"""Workflow authorization helpers."""

from app.auth.permissions import require_roles
from app.common.enums import UserRole

require_workflow_actor = require_roles(UserRole.ADMIN, UserRole.DISPATCHER, UserRole.DRIVER)
