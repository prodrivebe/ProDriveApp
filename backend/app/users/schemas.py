"""User API schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.common.enums import UserRole


class UserResponse(BaseModel):
    """Public user profile payload."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    first_name: str
    last_name: str
    email: EmailStr
    role: UserRole
    is_active: bool
    last_login: datetime | None
    created_at: datetime
    updated_at: datetime


class UserCreateRequest(BaseModel):
    """Create user request payload."""

    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: UserRole
    is_active: bool = True


class UserUpdateRequest(BaseModel):
    """Admin user update request payload."""

    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    role: UserRole
    is_active: bool = True


class ProfileUpdateRequest(BaseModel):
    """Self-service profile update payload."""

    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    email: EmailStr


class ProfilePasswordUpdateRequest(BaseModel):
    """Self-service password update payload."""

    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)
