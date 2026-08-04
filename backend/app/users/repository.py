"""User persistence layer."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.common.enums import UserRole
from app.users.models import User
from app.users.schemas import ProfileUpdateRequest, UserCreateRequest, UserUpdateRequest


class UserRepository:
    """Repository for user records."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_id(self, user_id: uuid.UUID) -> User | None:
        """Return an active user by identifier."""
        statement = select(User).where(
            User.id == user_id,
            User.deleted_at.is_(None),
        )
        return self._db.scalar(statement)

    def get_by_id_for_company(
        self,
        user_id: uuid.UUID,
        company_id: uuid.UUID,
    ) -> User | None:
        """Return an active user scoped to a company."""
        statement = select(User).where(
            User.id == user_id,
            User.company_id == company_id,
            User.deleted_at.is_(None),
        )
        return self._db.scalar(statement)

    def get_by_email(self, email: str) -> list[User]:
        """Return active users matching an email address."""
        statement = select(User).where(
            User.email == email.lower(),
            User.deleted_at.is_(None),
        )
        return list(self._db.scalars(statement).all())

    def get_by_email_for_company(
        self,
        email: str,
        company_id: uuid.UUID,
    ) -> User | None:
        """Return an active user by email within a company."""
        statement = select(User).where(
            User.email == email.lower(),
            User.company_id == company_id,
            User.deleted_at.is_(None),
        )
        return self._db.scalar(statement)

    def list_for_company(
        self,
        company_id: uuid.UUID,
        *,
        page: int,
        page_size: int,
        role: UserRole | None = None,
        search: str | None = None,
    ) -> tuple[list[User], int]:
        """Return paginated users for a company."""
        filters = [
            User.company_id == company_id,
            User.deleted_at.is_(None),
        ]
        if role is not None:
            filters.append(User.role == role)
        if search:
            pattern = f"%{search.strip()}%"
            filters.append(
                (User.first_name.ilike(pattern))
                | (User.last_name.ilike(pattern))
                | (User.email.ilike(pattern))
            )

        count_statement = select(func.count()).select_from(User).where(*filters)
        total = int(self._db.scalar(count_statement) or 0)

        offset = (page - 1) * page_size
        statement = (
            select(User)
            .where(*filters)
            .order_by(User.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        users = list(self._db.scalars(statement).all())
        return users, total

    def list_by_roles(
        self,
        company_id: uuid.UUID,
        roles: set[UserRole],
    ) -> list[User]:
        """Return active users in a company with any of the given roles."""
        statement = select(User).where(
            User.company_id == company_id,
            User.role.in_(roles),
            User.is_active.is_(True),
            User.deleted_at.is_(None),
        )
        return list(self._db.scalars(statement).all())

    def count_active_admins(self, company_id: uuid.UUID) -> int:
        """Count active admin users in a company."""
        statement = (
            select(func.count())
            .select_from(User)
            .where(
                User.company_id == company_id,
                User.role == UserRole.ADMIN,
                User.is_active.is_(True),
                User.deleted_at.is_(None),
            )
        )
        return int(self._db.scalar(statement) or 0)

    def update_password(self, user: User, password_hash: str) -> User:
        """Update a user's password hash."""
        user.password_hash = password_hash
        self._db.add(user)
        self._db.commit()
        self._db.refresh(user)
        return user

    def update_last_login(self, user: User) -> User:
        """Persist the latest login timestamp."""
        user.last_login = datetime.now(tz=UTC)
        self._db.add(user)
        self._db.commit()
        self._db.refresh(user)
        return user

    def create(
        self,
        *,
        company_id: uuid.UUID,
        payload: UserCreateRequest,
        password_hash: str,
        created_by: uuid.UUID | None,
    ) -> User:
        """Create a new user record."""
        user = User(
            company_id=company_id,
            first_name=payload.first_name,
            last_name=payload.last_name,
            email=str(payload.email).lower(),
            password_hash=password_hash,
            role=payload.role,
            is_active=payload.is_active,
            created_by=created_by,
            updated_by=created_by,
        )
        self._db.add(user)
        self._db.commit()
        self._db.refresh(user)
        return user

    def update(
        self,
        user: User,
        payload: UserUpdateRequest,
        updated_by: uuid.UUID,
    ) -> User:
        """Update a user record."""
        user.first_name = payload.first_name
        user.last_name = payload.last_name
        user.email = str(payload.email).lower()
        user.role = payload.role
        user.is_active = payload.is_active
        user.updated_by = updated_by
        self._db.add(user)
        self._db.commit()
        self._db.refresh(user)
        return user

    def update_profile(
        self,
        user: User,
        payload: ProfileUpdateRequest,
    ) -> User:
        """Update a user's own profile fields."""
        user.first_name = payload.first_name
        user.last_name = payload.last_name
        user.email = str(payload.email).lower()
        user.updated_by = user.id
        self._db.add(user)
        self._db.commit()
        self._db.refresh(user)
        return user

    def soft_delete(self, user: User, deleted_by: uuid.UUID) -> User:
        """Soft delete a user record."""
        user.deleted_at = datetime.now(tz=UTC)
        user.is_active = False
        user.updated_by = deleted_by
        self._db.add(user)
        self._db.commit()
        self._db.refresh(user)
        return user
