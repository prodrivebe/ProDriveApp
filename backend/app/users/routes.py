"""User API routes."""

import uuid

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.common.enums import UserRole
from app.common.pagination import build_list_meta
from app.common.responses import SuccessResponse, success_response
from app.database.session import get_db
from app.users.models import User
from app.users.permissions import require_user_admin
from app.users.schemas import (
    ProfilePasswordUpdateRequest,
    ProfileUpdateRequest,
    UserCreateRequest,
    UserResponse,
    UserUpdateRequest,
)
from app.users.service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


def get_client_ip(request: Request) -> str | None:
    """Extract the client IP address from the request."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    if request.client is not None:
        return request.client.host
    return None


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    """Provide a user service instance."""
    return UserService(db)


@router.get("", response_model=SuccessResponse[list[UserResponse]])
def list_users(
    request: Request,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    role: UserRole | None = Query(default=None),
    search: str | None = Query(default=None),
    current_user: User = Depends(require_user_admin),
    user_service: UserService = Depends(get_user_service),
) -> SuccessResponse[list[UserResponse]]:
    """List users for the current company."""
    users, total = user_service.list_users(
        current_user,
        page=page,
        page_size=page_size,
        role=role,
        search=search,
        ip_address=get_client_ip(request),
    )
    data = [UserResponse.model_validate(user) for user in users]
    return success_response(data, meta=build_list_meta(page, page_size, total))


@router.post("", response_model=SuccessResponse[UserResponse], status_code=201)
def create_user(
    payload: UserCreateRequest,
    request: Request,
    current_user: User = Depends(require_user_admin),
    user_service: UserService = Depends(get_user_service),
) -> SuccessResponse[UserResponse]:
    """Create a user in the current company."""
    user = user_service.create_user(
        current_user,
        payload,
        get_client_ip(request),
    )
    return success_response(UserResponse.model_validate(user))


@router.get("/me", response_model=SuccessResponse[UserResponse])
def get_my_profile(
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[UserResponse]:
    """Return the authenticated user's profile."""
    return success_response(UserResponse.model_validate(current_user))


@router.put("/me", response_model=SuccessResponse[UserResponse])
def update_my_profile(
    payload: ProfileUpdateRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
) -> SuccessResponse[UserResponse]:
    """Update the authenticated user's profile."""
    user = user_service.update_profile(
        current_user,
        payload,
        get_client_ip(request),
    )
    return success_response(UserResponse.model_validate(user))


@router.put("/me/password", response_model=SuccessResponse[dict[str, str]])
def update_my_password(
    payload: ProfilePasswordUpdateRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
) -> SuccessResponse[dict[str, str]]:
    """Update the authenticated user's password."""
    user_service.update_profile_password(
        current_user,
        payload,
        get_client_ip(request),
    )
    return success_response({"message": "Password updated successfully."})


@router.get("/{user_id}", response_model=SuccessResponse[UserResponse])
def get_user(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
) -> SuccessResponse[UserResponse]:
    """Return a user in the current company."""
    user = user_service.get_user(current_user, user_id)
    return success_response(UserResponse.model_validate(user))


@router.put("/{user_id}", response_model=SuccessResponse[UserResponse])
def update_user(
    user_id: uuid.UUID,
    payload: UserUpdateRequest,
    request: Request,
    current_user: User = Depends(require_user_admin),
    user_service: UserService = Depends(get_user_service),
) -> SuccessResponse[UserResponse]:
    """Update a user in the current company."""
    user = user_service.update_user(
        current_user,
        user_id,
        payload,
        get_client_ip(request),
    )
    return success_response(UserResponse.model_validate(user))


@router.delete("/{user_id}", response_model=SuccessResponse[dict[str, str]])
def delete_user(
    user_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(require_user_admin),
    user_service: UserService = Depends(get_user_service),
) -> SuccessResponse[dict[str, str]]:
    """Soft delete a user in the current company."""
    user_service.delete_user(
        current_user,
        user_id,
        get_client_ip(request),
    )
    return success_response({"message": "User deleted successfully."})
