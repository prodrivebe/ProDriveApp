"""Notification API schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class NotificationResponse(BaseModel):
    """Notification response payload."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    user_id: uuid.UUID
    title: str
    message: str
    type: str
    read_at: datetime | None
    created_at: datetime


class DeviceTokenRegisterRequest(BaseModel):
    """Register a push notification device token."""

    token: str = Field(min_length=1, max_length=512)
    platform: str = Field(default="android", max_length=32)


class DeviceTokenResponse(BaseModel):
    """Registered device token response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    platform: str
    created_at: datetime
    updated_at: datetime
