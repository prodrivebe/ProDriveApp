"""Authentication input validation."""

import re

from app.common.exceptions import ValidationError

PASSWORD_PATTERN = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).+$",
)


def validate_password_strength(password: str) -> None:
    """Validate password complexity requirements."""
    if len(password) < 8:
        raise ValidationError(
            code="WEAK_PASSWORD",
            message="Password must be at least 8 characters long.",
        )
    if not PASSWORD_PATTERN.match(password):
        raise ValidationError(
            code="WEAK_PASSWORD",
            message=(
                "Password must contain at least one uppercase letter, "
                "one lowercase letter, and one number."
            ),
        )
