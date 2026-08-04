"""Authentication request and response schemas."""

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Login credentials."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class TokenResponse(BaseModel):
    """JWT token pair response payload."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    """Refresh token request payload."""

    refresh_token: str = Field(min_length=20)


class LogoutRequest(BaseModel):
    """Logout request payload."""

    refresh_token: str = Field(min_length=20)


class PasswordResetRequest(BaseModel):
    """Password reset request payload."""

    email: EmailStr


class PasswordResetConfirmRequest(BaseModel):
    """Password reset confirmation payload."""

    token: str = Field(min_length=20)
    new_password: str = Field(min_length=8, max_length=128)


class PasswordResetRequestResponse(BaseModel):
    """Password reset request acknowledgement."""

    message: str
