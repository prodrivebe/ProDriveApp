"""Authentication FastAPI dependencies."""

import uuid

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.auth.security import decode_jwt_token
from app.common.exceptions import AuthenticationError
from app.config.settings import Settings, get_settings
from app.database.session import get_db
from app.users.models import User
from app.users.repository import UserRepository

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> User:
    """Resolve the authenticated user from a bearer access token."""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AuthenticationError(
            code="UNAUTHORIZED",
            message="Authentication credentials were not provided.",
        )

    try:
        payload = decode_jwt_token(credentials.credentials, settings)
    except Exception as exc:
        raise AuthenticationError(
            code="INVALID_TOKEN",
            message="Access token is invalid or expired.",
        ) from exc

    if payload.get("type") != "access":
        raise AuthenticationError(
            code="INVALID_TOKEN",
            message="Access token is invalid or expired.",
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise AuthenticationError(
            code="INVALID_TOKEN",
            message="Access token is invalid or expired.",
        )

    user = UserRepository(db).get_by_id(uuid.UUID(str(user_id)))
    if user is None or not user.is_active:
        raise AuthenticationError(
            code="UNAUTHORIZED",
            message="User account is inactive or does not exist.",
        )

    return user
