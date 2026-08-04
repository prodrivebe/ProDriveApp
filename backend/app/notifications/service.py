"""Notification business logic."""

import uuid

from sqlalchemy.orm import Session

from app.common.enums import UserRole
from app.common.exceptions import NotFoundError
from app.notifications.models import DeviceToken, Notification
from app.notifications.device_token_repository import DeviceTokenRepository
from app.notifications.repository import NotificationRepository
from app.users.models import User
from app.users.repository import UserRepository


class NotificationService:
    """In-app notification workflows."""

    def __init__(self, db: Session) -> None:
        self._repository = NotificationRepository(db)
        self._device_tokens = DeviceTokenRepository(db)
        self._users = UserRepository(db)

    def list_notifications(
        self,
        current_user: User,
        *,
        unread_only: bool = False,
    ) -> list[Notification]:
        """List notifications for the current user."""
        return self._repository.list_for_user(
            current_user.id,
            current_user.company_id,
            unread_only=unread_only,
        )

    def mark_read(self, current_user: User, notification_id: uuid.UUID) -> Notification:
        """Mark a notification as read."""
        notification = self._repository.get_by_id_for_user(
            notification_id,
            current_user.id,
            current_user.company_id,
        )
        if notification is None:
            raise NotFoundError(
                code="NOTIFICATION_NOT_FOUND",
                message="Notification not found.",
            )
        if notification.read_at is not None:
            return notification
        return self._repository.mark_read(notification)

    def mark_all_read(self, current_user: User) -> int:
        """Mark all notifications as read."""
        return self._repository.mark_all_read(current_user.id, current_user.company_id)

    def count_unread(self, current_user: User) -> int:
        """Return unread notification count for the current user."""
        return self._repository.count_unread(current_user.id, current_user.company_id)

    def notify_user(
        self,
        *,
        company_id: uuid.UUID,
        user_id: uuid.UUID,
        title: str,
        message: str,
        notification_type: str,
    ) -> Notification:
        """Create a notification for a user."""
        return self._repository.create(
            company_id=company_id,
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
        )

    def notify_staff(
        self,
        *,
        company_id: uuid.UUID,
        roles: set[UserRole],
        title: str,
        message: str,
        notification_type: str,
    ) -> list[Notification]:
        """Create notifications for company staff with the given roles."""
        staff = self._users.list_by_roles(company_id, roles)
        notifications: list[Notification] = []
        for user in staff:
            notifications.append(
                self.notify_user(
                    company_id=company_id,
                    user_id=user.id,
                    title=title,
                    message=message,
                    notification_type=notification_type,
                )
            )
        return notifications

    def register_device(
        self,
        current_user: User,
        *,
        token: str,
        platform: str,
    ) -> DeviceToken:
        """Register or refresh a push notification device token."""
        return self._device_tokens.upsert(
            company_id=current_user.company_id,
            user_id=current_user.id,
            token=token,
            platform=platform,
        )
