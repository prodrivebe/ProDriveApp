"""Company input validation."""

import re

from app.common.exceptions import ValidationError

CURRENCY_CODE_PATTERN = re.compile(r"^[A-Z]{3}$")


def validate_currency_code(currency_code: str) -> None:
    """Validate ISO 4217 currency code format."""
    normalized = currency_code.upper()
    if not CURRENCY_CODE_PATTERN.match(normalized):
        raise ValidationError(
            code="INVALID_CURRENCY",
            message="Currency code must be a 3-letter ISO code.",
        )
