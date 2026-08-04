"""Tenant isolation helpers."""

import uuid

from app.common.exceptions import AuthorizationError, NotFoundError
from app.users.models import User


def get_user_company_id(user: User) -> uuid.UUID:
    """Return the company identifier for the authenticated user."""
    return user.company_id


def ensure_same_company(
    resource_company_id: uuid.UUID,
    current_user: User,
) -> None:
    """Ensure a resource belongs to the authenticated user's company."""
    if resource_company_id != current_user.company_id:
        raise AuthorizationError(
            code="FORBIDDEN",
            message="Cross-company access is not allowed.",
        )


def ensure_company_match(
    requested_company_id: uuid.UUID,
    current_user: User,
) -> None:
    """Ensure a requested company identifier matches the current tenant."""
    if requested_company_id != current_user.company_id:
        raise NotFoundError(
            code="COMPANY_NOT_FOUND",
            message="Company not found.",
        )
