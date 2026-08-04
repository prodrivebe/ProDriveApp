"""Authentication persistence layer."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.models import PasswordResetToken, RefreshToken


class AuthRepository:
    """Repository for authentication token records."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def create_refresh_token(
        self,
        *,
        user_id: uuid.UUID,
        token_hash: str,
        expires_at: datetime,
        ip_address: str | None,
    ) -> RefreshToken:
        """Persist a refresh token record."""
        refresh_token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            ip_address=ip_address,
        )
        self._db.add(refresh_token)
        self._db.commit()
        self._db.refresh(refresh_token)
        return refresh_token

    def get_refresh_token_by_hash(self, token_hash: str) -> RefreshToken | None:
        """Return a refresh token by hash."""
        statement = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        return self._db.scalar(statement)

    def revoke_refresh_token(self, refresh_token: RefreshToken) -> None:
        """Revoke a refresh token."""
        refresh_token.revoked_at = datetime.now(tz=UTC)
        self._db.add(refresh_token)
        self._db.commit()

    def revoke_all_user_refresh_tokens(self, user_id: uuid.UUID) -> None:
        """Revoke all active refresh tokens for a user."""
        statement = select(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked_at.is_(None),
        )
        tokens = self._db.scalars(statement).all()
        revoked_at = datetime.now(tz=UTC)
        for token in tokens:
            token.revoked_at = revoked_at
            self._db.add(token)
        self._db.commit()

    def create_password_reset_token(
        self,
        *,
        user_id: uuid.UUID,
        token_hash: str,
        expires_at: datetime,
    ) -> PasswordResetToken:
        """Persist a password reset token."""
        reset_token = PasswordResetToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        self._db.add(reset_token)
        self._db.commit()
        self._db.refresh(reset_token)
        return reset_token

    def get_password_reset_token_by_hash(
        self,
        token_hash: str,
    ) -> PasswordResetToken | None:
        """Return a password reset token by hash."""
        statement = select(PasswordResetToken).where(
            PasswordResetToken.token_hash == token_hash,
        )
        return self._db.scalar(statement)

    def mark_password_reset_token_used(
        self,
        reset_token: PasswordResetToken,
    ) -> None:
        """Mark a password reset token as used."""
        reset_token.used_at = datetime.now(tz=UTC)
        self._db.add(reset_token)
        self._db.commit()
