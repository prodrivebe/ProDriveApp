"""Notification persistence layer."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.notifications.models import Notification


class NotificationRepository:
    """Repository for notification records."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def list_for_user(
        self,
        user_id: uuid.UUID,
        company_id: uuid.UUID,
        *,
        unread_only: bool = False,
    ) -> list[Notification]:
        """Return notifications for a user."""
        filters = [
            Notification.user_id == user_id,
            Notification.company_id == company_id,
        ]
        if unread_only:
            filters.append(Notification.read_at.is_(None))
        statement = (
            select(Notification)
            .where(*filters)
            .order_by(Notification.created_at.desc())
        )
        return list(self._db.scalars(statement).all())

    def count_unread(self, user_id: uuid.UUID, company_id: uuid.UUID) -> int:
        """Return unread notification count."""
        return int(
            self._db.scalar(
                select(func.count())
                .select_from(Notification)
                .where(
                    Notification.user_id == user_id,
                    Notification.company_id == company_id,
                    Notification.read_at.is_(None),
                )
            )
            or 0
        )

    def get_by_id_for_user(
        self,
        notification_id: uuid.UUID,
        user_id: uuid.UUID,
        company_id: uuid.UUID,
    ) -> Notification | None:
        """Return a notification scoped to a user."""
        statement = select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user_id,
            Notification.company_id == company_id,
        )
        return self._db.scalar(statement)

    def create(
        self,
        *,
        company_id: uuid.UUID,
        user_id: uuid.UUID,
        title: str,
        message: str,
        notification_type: str,
        order_id: uuid.UUID | None = None,
    ) -> Notification:
        """Create a notification."""
        notification = Notification(
            company_id=company_id,
            user_id=user_id,
            title=title,
            message=message,
            type=notification_type,
            order_id=order_id,
            created_at=datetime.now(tz=UTC),
        )
        self._db.add(notification)
        self._db.commit()
        self._db.refresh(notification)
        return notification

    def mark_read(self, notification: Notification) -> Notification:
        """Mark a notification as read."""
        notification.read_at = datetime.now(tz=UTC)
        self._db.add(notification)
        self._db.commit()
        self._db.refresh(notification)
        return notification

    def mark_all_read(self, user_id: uuid.UUID, company_id: uuid.UUID) -> int:
        """Mark all notifications as read for a user."""
        notifications = self.list_for_user(user_id, company_id, unread_only=True)
        now = datetime.now(tz=UTC)
        for notification in notifications:
            notification.read_at = now
            self._db.add(notification)
        self._db.commit()
        return len(notifications)
