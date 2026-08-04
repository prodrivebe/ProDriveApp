"""User business logic."""

import uuid

from sqlalchemy.orm import Session

from app.audit.service import AuditService
from app.auth.security import hash_password, verify_password
from app.auth.validators import validate_password_strength
from app.common.enums import UserRole
from app.common.exceptions import AuthorizationError, NotFoundError, ValidationError
from app.common.tenant import ensure_same_company
from app.users.models import User
from app.users.repository import UserRepository
from app.users.schemas import (
    ProfilePasswordUpdateRequest,
    ProfileUpdateRequest,
    UserCreateRequest,
    UserUpdateRequest,
)
from app.users.validators import (
    validate_admin_can_be_removed,
    validate_not_self_target,
    validate_user_creation_role,
)

DEFAULT_PAGE_SIZE = 25
MAX_PAGE_SIZE = 100


class UserService:
    """User management and profile workflows."""

    def __init__(self, db: Session) -> None:
        self._db = db
        self._repository = UserRepository(db)
        self._audit_service = AuditService(db)

    def list_users(
        self,
        current_user: User,
        *,
        page: int,
        page_size: int,
        role: UserRole | None,
        search: str | None,
        ip_address: str | None,
    ) -> tuple[list[User], int]:
        """List users for the current company."""
        normalized_page = max(page, 1)
        normalized_page_size = min(max(page_size, 1), MAX_PAGE_SIZE)
        users, total = self._repository.list_for_company(
            current_user.company_id,
            page=normalized_page,
            page_size=normalized_page_size,
            role=role,
            search=search,
        )
        return users, total

    def get_user(self, current_user: User, user_id: uuid.UUID) -> User:
        """Return a user visible to the current actor."""
        user = self._repository.get_by_id_for_company(user_id, current_user.company_id)
        if user is None:
            raise NotFoundError(
                code="USER_NOT_FOUND",
                message="User not found.",
            )

        if current_user.role != UserRole.ADMIN and user.id != current_user.id:
            raise AuthorizationError(
                code="FORBIDDEN",
                message="You do not have permission to view this user.",
            )
        ensure_same_company(user.company_id, current_user)
        return user

    def create_user(
        self,
        current_user: User,
        payload: UserCreateRequest,
        ip_address: str | None,
    ) -> User:
        """Create a user in the current company."""
        validate_user_creation_role(payload.role)
        validate_password_strength(payload.password)

        existing_user = self._repository.get_by_email_for_company(
            str(payload.email),
            current_user.company_id,
        )
        if existing_user is not None:
            raise ValidationError(
                code="EMAIL_ALREADY_EXISTS",
                message="A user with this email already exists in the company.",
            )

        user = self._repository.create(
            company_id=current_user.company_id,
            payload=payload,
            password_hash=hash_password(payload.password),
            created_by=current_user.id,
        )
        self._audit_service.record_user_created(
            company_id=current_user.company_id,
            user_id=current_user.id,
            entity_id=str(user.id),
            ip_address=ip_address,
        )
        return user

    def update_user(
        self,
        current_user: User,
        user_id: uuid.UUID,
        payload: UserUpdateRequest,
        ip_address: str | None,
    ) -> User:
        """Update a user in the current company."""
        user = self.get_user(current_user, user_id)
        if current_user.role != UserRole.ADMIN:
            raise AuthorizationError(
                code="FORBIDDEN",
                message="You do not have permission to update this user.",
            )

        if str(payload.email).lower() != user.email:
            existing_user = self._repository.get_by_email_for_company(
                str(payload.email),
                current_user.company_id,
            )
            if existing_user is not None and existing_user.id != user.id:
                raise ValidationError(
                    code="EMAIL_ALREADY_EXISTS",
                    message="A user with this email already exists in the company.",
                )

        if user.role == UserRole.ADMIN and payload.role != UserRole.ADMIN:
            active_admin_count = self._repository.count_active_admins(
                current_user.company_id,
            )
            validate_admin_can_be_removed(user, active_admin_count)

        if user.is_active and not payload.is_active and user.role == UserRole.ADMIN:
            active_admin_count = self._repository.count_active_admins(
                current_user.company_id,
            )
            validate_admin_can_be_removed(user, active_admin_count)

        updated_user = self._repository.update(user, payload, current_user.id)
        self._audit_service.record_user_updated(
            company_id=current_user.company_id,
            user_id=current_user.id,
            entity_id=str(user.id),
            ip_address=ip_address,
        )
        return updated_user

    def delete_user(
        self,
        current_user: User,
        user_id: uuid.UUID,
        ip_address: str | None,
    ) -> None:
        """Soft delete a user in the current company."""
        user = self.get_user(current_user, user_id)
        if current_user.role != UserRole.ADMIN:
            raise AuthorizationError(
                code="FORBIDDEN",
                message="You do not have permission to delete this user.",
            )

        validate_not_self_target(current_user.id, user.id)
        active_admin_count = self._repository.count_active_admins(current_user.company_id)
        validate_admin_can_be_removed(user, active_admin_count)

        self._repository.soft_delete(user, current_user.id)
        self._audit_service.record_user_deleted(
            company_id=current_user.company_id,
            user_id=current_user.id,
            entity_id=str(user.id),
            ip_address=ip_address,
        )

    def update_profile(
        self,
        current_user: User,
        payload: ProfileUpdateRequest,
        ip_address: str | None,
    ) -> User:
        """Update the authenticated user's profile."""
        if str(payload.email).lower() != current_user.email:
            existing_user = self._repository.get_by_email_for_company(
                str(payload.email),
                current_user.company_id,
            )
            if existing_user is not None and existing_user.id != current_user.id:
                raise ValidationError(
                    code="EMAIL_ALREADY_EXISTS",
                    message="A user with this email already exists in the company.",
                )

        updated_user = self._repository.update_profile(current_user, payload)
        self._audit_service.record_user_profile_updated(
            company_id=current_user.company_id,
            user_id=current_user.id,
            entity_id=str(current_user.id),
            ip_address=ip_address,
        )
        return updated_user

    def update_profile_password(
        self,
        current_user: User,
        payload: ProfilePasswordUpdateRequest,
        ip_address: str | None,
    ) -> None:
        """Update the authenticated user's password."""
        if not verify_password(payload.current_password, current_user.password_hash):
            raise ValidationError(
                code="INVALID_PASSWORD",
                message="Current password is incorrect.",
            )

        validate_password_strength(payload.new_password)
        password_hash = hash_password(payload.new_password)
        self._repository.update_password(current_user, password_hash)
        self._audit_service.record_user_password_updated(
            company_id=current_user.company_id,
            user_id=current_user.id,
            entity_id=str(current_user.id),
            ip_address=ip_address,
        )
