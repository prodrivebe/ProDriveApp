"""Authentication authorization helpers."""

from collections.abc import Callable

from fastapi import Depends

from app.auth.dependencies import get_current_user
from app.common.enums import UserRole
from app.common.exceptions import AuthorizationError
from app.users.models import User


def require_roles(*roles: UserRole) -> Callable[..., User]:
    """Return a dependency that enforces role-based access."""

    allowed_roles = set(roles)

    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise AuthorizationError(
                code="FORBIDDEN",
                message="You do not have permission to perform this action.",
            )
        return current_user

    return role_checker
