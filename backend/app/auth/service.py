"""Authentication business logic."""

from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.audit.service import AuditService
from app.auth.repository import AuthRepository
from app.auth.schemas import (
    LoginRequest,
    LogoutRequest,
    PasswordResetConfirmRequest,
    PasswordResetRequest,
    TokenResponse,
)
from app.auth.security import (
    create_jwt_token,
    ensure_utc,
    generate_secure_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.auth.validators import validate_password_strength
from app.common.exceptions import AuthenticationError, ValidationError
from app.config.settings import Settings
from app.users.models import User
from app.users.repository import UserRepository


class AuthService:
    """Authentication workflow service."""

    def __init__(self, db: Session, settings: Settings) -> None:
        self._db = db
        self._settings = settings
        self._users = UserRepository(db)
        self._auth_repository = AuthRepository(db)
        self._audit_service = AuditService(db)

    def login(
        self,
        payload: LoginRequest,
        ip_address: str | None,
    ) -> TokenResponse:
        """Authenticate a user and issue token pair."""
        users = self._users.get_by_login_identifier(payload.username)
        if len(users) != 1:
            raise AuthenticationError(
                code="INVALID_CREDENTIALS",
                message="Invalid username or password.",
            )

        user = users[0]
        if not user.is_active or not verify_password(payload.password, user.password_hash):
            self._audit_service.record_login(
                company_id=user.company_id,
                user_id=user.id,
                ip_address=ip_address,
                success=False,
            )
            raise AuthenticationError(
                code="INVALID_CREDENTIALS",
                message="Invalid username or password.",
            )

        token_response = self._issue_token_pair(user, ip_address)
        self._users.update_last_login(user)
        self._audit_service.record_login(
            company_id=user.company_id,
            user_id=user.id,
            ip_address=ip_address,
            success=True,
        )
        return token_response

    def refresh(
        self,
        refresh_token: str,
        ip_address: str | None,
    ) -> TokenResponse:
        """Rotate refresh token and issue a new token pair."""
        stored_token = self._auth_repository.get_refresh_token_by_hash(
            hash_token(refresh_token),
        )
        if stored_token is None:
            raise AuthenticationError(
                code="INVALID_TOKEN",
                message="Refresh token is invalid or expired.",
            )

        now = datetime.now(tz=UTC)
        expires_at = ensure_utc(stored_token.expires_at)
        if stored_token.revoked_at is not None or expires_at <= now:
            raise AuthenticationError(
                code="INVALID_TOKEN",
                message="Refresh token is invalid or expired.",
            )

        user = self._users.get_by_id(stored_token.user_id)
        if user is None or not user.is_active:
            raise AuthenticationError(
                code="UNAUTHORIZED",
                message="User account is inactive or does not exist.",
            )

        self._auth_repository.revoke_refresh_token(stored_token)
        return self._issue_token_pair(user, ip_address)

    def logout(
        self,
        payload: LogoutRequest,
        current_user: User,
        ip_address: str | None,
    ) -> None:
        """Revoke a refresh token and record logout."""
        stored_token = self._auth_repository.get_refresh_token_by_hash(
            hash_token(payload.refresh_token),
        )
        if (
            stored_token is not None
            and stored_token.user_id == current_user.id
            and stored_token.revoked_at is None
        ):
            self._auth_repository.revoke_refresh_token(stored_token)

        self._audit_service.record_logout(
            company_id=current_user.company_id,
            user_id=current_user.id,
            ip_address=ip_address,
        )

    def request_password_reset(
        self,
        payload: PasswordResetRequest,
        ip_address: str | None,
    ) -> tuple[str, str | None]:
        """Create a password reset token when the account exists."""
        users = self._users.get_by_email(payload.email)
        reset_token: str | None = None
        message = (
            "If an account with that email exists, "
            "password reset instructions have been sent."
        )

        if len(users) == 1:
            user = users[0]
            raw_token = generate_secure_token()
            expires_at = datetime.now(tz=UTC) + timedelta(
                hours=self._settings.password_reset_token_expire_hours,
            )
            self._auth_repository.create_password_reset_token(
                user_id=user.id,
                token_hash=hash_token(raw_token),
                expires_at=expires_at,
            )
            self._audit_service.record_password_reset_requested(
                company_id=user.company_id,
                user_id=user.id,
                ip_address=ip_address,
            )
            reset_token = raw_token

        return message, reset_token

    def confirm_password_reset(
        self,
        payload: PasswordResetConfirmRequest,
        ip_address: str | None,
    ) -> None:
        """Reset a user password using a valid reset token."""
        validate_password_strength(payload.new_password)

        stored_token = self._auth_repository.get_password_reset_token_by_hash(
            hash_token(payload.token),
        )
        now = datetime.now(tz=UTC)
        expires_at = (
            ensure_utc(stored_token.expires_at) if stored_token is not None else now
        )
        if (
            stored_token is None
            or stored_token.used_at is not None
            or expires_at <= now
        ):
            raise ValidationError(
                code="INVALID_RESET_TOKEN",
                message="Password reset token is invalid or expired.",
            )

        user = self._users.get_by_id(stored_token.user_id)
        if user is None or not user.is_active:
            raise ValidationError(
                code="INVALID_RESET_TOKEN",
                message="Password reset token is invalid or expired.",
            )

        password_hash = hash_password(payload.new_password)
        self._users.update_password(user, password_hash)
        self._auth_repository.mark_password_reset_token_used(stored_token)
        self._auth_repository.revoke_all_user_refresh_tokens(user.id)
        self._audit_service.record_password_reset_completed(
            company_id=user.company_id,
            user_id=user.id,
            ip_address=ip_address,
        )

    def _issue_token_pair(
        self,
        user: User,
        ip_address: str | None,
    ) -> TokenResponse:
        """Create and persist a new access and refresh token pair."""
        access_token, _ = create_jwt_token(
            settings=self._settings,
            user_id=user.id,
            company_id=user.company_id,
            role=user.role,
            token_type="access",
        )

        refresh_token_value = generate_secure_token()
        expires_at = datetime.now(tz=UTC) + timedelta(
            days=self._settings.jwt_refresh_token_expire_days,
        )
        self._auth_repository.create_refresh_token(
            user_id=user.id,
            token_hash=hash_token(refresh_token_value),
            expires_at=expires_at,
            ip_address=ip_address,
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token_value,
            expires_in=self._settings.jwt_access_token_expire_minutes * 60,
        )
