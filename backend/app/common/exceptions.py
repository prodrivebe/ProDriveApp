"""Application exception types."""


class AppException(Exception):
    """Base application exception with API error metadata."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
    ) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class AuthenticationError(AppException):
    """Raised when authentication fails."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(code=code, message=message, status_code=401)


class AuthorizationError(AppException):
    """Raised when the user lacks required permissions."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(code=code, message=message, status_code=403)


class NotFoundError(AppException):
    """Raised when a requested resource does not exist."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(code=code, message=message, status_code=404)


class ValidationError(AppException):
    """Raised when input validation fails."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(code=code, message=message, status_code=422)
