"""Notification API routes."""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.common.responses import SuccessResponse, success_response
from app.database.session import get_db
from app.notifications.schemas import (
    DeviceTokenRegisterRequest,
    DeviceTokenResponse,
    NotificationResponse,
)
from app.notifications.service import NotificationService
from app.users.models import User

router = APIRouter(prefix="/notifications", tags=["Notifications"])


def get_notification_service(db: Session = Depends(get_db)) -> NotificationService:
    """Provide a notification service instance."""
    return NotificationService(db)


@router.get("", response_model=SuccessResponse[list[NotificationResponse]])
def list_notifications(
    unread_only: bool = Query(default=False),
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service),
) -> SuccessResponse[list[NotificationResponse]]:
    """List notifications for the current user."""
    notifications = notification_service.list_notifications(
        current_user,
        unread_only=unread_only,
    )
    return success_response(
        [NotificationResponse.model_validate(notification) for notification in notifications]
    )


@router.post("/{notification_id}/read", response_model=SuccessResponse[NotificationResponse])
def mark_notification_read(
    notification_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service),
) -> SuccessResponse[NotificationResponse]:
    """Mark a notification as read."""
    notification = notification_service.mark_read(current_user, notification_id)
    return success_response(NotificationResponse.model_validate(notification))


@router.post("/read-all", response_model=SuccessResponse[dict[str, int]])
def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service),
) -> SuccessResponse[dict[str, int]]:
    """Mark all notifications as read."""
    updated_count = notification_service.mark_all_read(current_user)
    return success_response({"updated_count": updated_count})


@router.post(
    "/register-device",
    response_model=SuccessResponse[DeviceTokenResponse],
    status_code=201,
)
def register_device(
    payload: DeviceTokenRegisterRequest,
    current_user: User = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service),
) -> SuccessResponse[DeviceTokenResponse]:
    """Register a device for future push notifications."""
    device_token = notification_service.register_device(
        current_user,
        token=payload.token,
        platform=payload.platform,
    )
    return success_response(DeviceTokenResponse.model_validate(device_token))
