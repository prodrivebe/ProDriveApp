"""Authentication API routes."""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.permissions import require_roles
from app.auth.schemas import (
    LoginRequest,
    LogoutRequest,
    PasswordResetConfirmRequest,
    PasswordResetRequest,
    PasswordResetRequestResponse,
    RefreshRequest,
    TokenResponse,
)
from app.auth.service import AuthService
from app.common.enums import UserRole
from app.common.responses import SuccessResponse, success_response
from app.config.settings import Settings, get_settings
from app.database.session import get_db
from app.users.models import User
from app.users.schemas import UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


def get_client_ip(request: Request) -> str | None:
    """Extract the client IP address from the request."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    if request.client is not None:
        return request.client.host
    return None


def get_auth_service(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> AuthService:
    """Provide an authentication service instance."""
    return AuthService(db, settings)


@router.post("/login", response_model=SuccessResponse[TokenResponse])
def login(
    payload: LoginRequest,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
) -> SuccessResponse[TokenResponse]:
    """Authenticate a user and return JWT tokens."""
    tokens = auth_service.login(payload, get_client_ip(request))
    return success_response(tokens)


@router.post("/refresh", response_model=SuccessResponse[TokenResponse])
def refresh_tokens(
    payload: RefreshRequest,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
) -> SuccessResponse[TokenResponse]:
    """Issue a new token pair using a refresh token."""
    tokens = auth_service.refresh(payload.refresh_token, get_client_ip(request))
    return success_response(tokens)


@router.post("/logout", response_model=SuccessResponse[dict[str, str]])
def logout(
    payload: LogoutRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> SuccessResponse[dict[str, str]]:
    """Revoke refresh token and end the session."""
    auth_service.logout(payload, current_user, get_client_ip(request))
    return success_response({"message": "Logged out successfully."})


@router.get("/me", response_model=SuccessResponse[UserResponse])
def get_current_profile(
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[UserResponse]:
    """Return the authenticated user profile."""
    return success_response(UserResponse.model_validate(current_user))


@router.post(
    "/password-reset/request",
    response_model=SuccessResponse[PasswordResetRequestResponse],
)
def request_password_reset(
    payload: PasswordResetRequest,
    request: Request,
    settings: Settings = Depends(get_settings),
    auth_service: AuthService = Depends(get_auth_service),
) -> SuccessResponse[PasswordResetRequestResponse]:
    """Request a password reset token."""
    message, reset_token = auth_service.request_password_reset(
        payload,
        get_client_ip(request),
    )
    meta: dict[str, str] = {}
    if settings.debug and reset_token is not None:
        meta["reset_token"] = reset_token
    return success_response(PasswordResetRequestResponse(message=message), meta=meta)


@router.post("/password-reset/confirm", response_model=SuccessResponse[dict[str, str]])
def confirm_password_reset(
    payload: PasswordResetConfirmRequest,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
) -> SuccessResponse[dict[str, str]]:
    """Confirm password reset with a valid token."""
    auth_service.confirm_password_reset(payload, get_client_ip(request))
    return success_response({"message": "Password updated successfully."})


@router.get(
    "/admin-check",
    response_model=SuccessResponse[dict[str, str]],
    include_in_schema=False,
)
def admin_check(
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
) -> SuccessResponse[dict[str, str]]:
    """Internal endpoint used to verify role-based authorization."""
    return success_response({"role": current_user.role.value})
