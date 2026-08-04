"""Device token persistence layer."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.notifications.models import DeviceToken


class DeviceTokenRepository:
    """Repository for push device tokens."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def upsert(
        self,
        *,
        company_id: uuid.UUID,
        user_id: uuid.UUID,
        token: str,
        platform: str,
    ) -> DeviceToken:
        """Create or update a device token."""
        statement = select(DeviceToken).where(
            DeviceToken.user_id == user_id,
            DeviceToken.token == token,
        )
        existing = self._db.scalar(statement)
        now = datetime.now(tz=UTC)
        if existing is not None:
            existing.platform = platform
            existing.updated_at = now
            self._db.add(existing)
            self._db.commit()
            self._db.refresh(existing)
            return existing

        device_token = DeviceToken(
            company_id=company_id,
            user_id=user_id,
            token=token,
            platform=platform,
            created_at=now,
            updated_at=now,
        )
        self._db.add(device_token)
        self._db.commit()
        self._db.refresh(device_token)
        return device_token
