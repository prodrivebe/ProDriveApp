"""Driver validation helpers."""

import uuid

from app.common.enums import UserRole
from app.common.exceptions import ValidationError
from app.users.models import User


def validate_driver_user(user: User, company_id: uuid.UUID) -> None:
    """Ensure the linked user can have a driver profile."""
    if user.company_id != company_id:
        raise ValidationError(
            code="INVALID_DRIVER_USER",
            message="User must belong to the same company.",
        )
    if user.role != UserRole.DRIVER:
        raise ValidationError(
            code="INVALID_DRIVER_USER",
            message="User must have the DRIVER role.",
        )
    if not user.is_active or user.deleted_at is not None:
        raise ValidationError(
            code="INVALID_DRIVER_USER",
            message="User must be active.",
        )


def validate_unique_driver_user(existing_driver_id: uuid.UUID | None, user_id: uuid.UUID) -> None:
    """Ensure a user does not already have a driver profile."""
    if existing_driver_id is not None:
        raise ValidationError(
            code="DRIVER_ALREADY_EXISTS",
            message="This user already has a driver profile.",
        )
