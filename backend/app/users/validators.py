"""User input validation."""

import uuid

from app.common.enums import UserRole
from app.common.exceptions import ValidationError
from app.users.models import User


def validate_user_creation_role(role: UserRole) -> None:
    """Ensure the role is allowed during user creation."""
    if role not in {UserRole.ADMIN, UserRole.DISPATCHER, UserRole.DRIVER}:
        raise ValidationError(
            code="INVALID_ROLE",
            message="Role must be ADMIN, DISPATCHER, or DRIVER.",
        )


def validate_not_self_target(current_user_id: uuid.UUID, target_user_id: uuid.UUID) -> None:
    """Prevent destructive actions against the current user."""
    if current_user_id == target_user_id:
        raise ValidationError(
            code="INVALID_OPERATION",
            message="You cannot perform this action on your own account.",
        )


def validate_admin_can_be_removed(user: User, active_admin_count: int) -> None:
    """Prevent removing the last active admin."""
    if user.role == UserRole.ADMIN and user.is_active and active_admin_count <= 1:
        raise ValidationError(
            code="LAST_ADMIN",
            message="At least one active admin must remain in the company.",
        )
