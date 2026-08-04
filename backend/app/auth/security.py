"""Authentication security helpers."""

import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, Literal

import bcrypt
import jwt

from app.common.enums import UserRole
from app.config.settings import Settings

TokenType = Literal["access", "refresh"]


def ensure_utc(value: datetime) -> datetime:
    """Normalize datetimes to UTC."""
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def generate_secure_token() -> str:
    """Generate a URL-safe secure token."""
    return secrets.token_urlsafe(48)


def hash_token(token: str) -> str:
    """Hash a token for storage."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_jwt_token(
    *,
    settings: Settings,
    user_id: uuid.UUID,
    company_id: uuid.UUID,
    role: UserRole,
    token_type: TokenType,
    token_id: uuid.UUID | None = None,
) -> tuple[str, datetime]:
    """Create a signed JWT access or refresh token."""
    now = datetime.now(tz=UTC)
    if token_type == "access":
        expires_at = now + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    else:
        expires_at = now + timedelta(days=settings.jwt_refresh_token_expire_days)

    payload: dict[str, Any] = {
        "sub": str(user_id),
        "company_id": str(company_id),
        "role": role.value,
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
        "jti": str(token_id or uuid.uuid4()),
    }
    token = jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    return token, expires_at


def decode_jwt_token(token: str, settings: Settings) -> dict[str, Any]:
    """Decode and validate a JWT token."""
    return jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )
