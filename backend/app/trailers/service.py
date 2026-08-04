"""Trailer business logic."""

import uuid

from sqlalchemy.orm import Session

from app.common.exceptions import NotFoundError, ValidationError
from app.common.tenant import ensure_same_company
from app.trailers.models import Trailer
from app.trailers.repository import TrailerRepository
from app.trailers.schemas import TrailerCreateRequest, TrailerUpdateRequest
from app.trailers.validators import validate_trailer_capacity
from app.users.models import User

MAX_PAGE_SIZE = 100


class TrailerService:
    """Trailer management workflows."""

    def __init__(self, db: Session) -> None:
        self._db = db
        self._repository = TrailerRepository(db)

    def list_trailers(
        self,
        current_user: User,
        *,
        page: int,
        page_size: int,
        active: bool | None,
        search: str | None,
    ) -> tuple[list[Trailer], int]:
        """List trailers for the current company."""
        normalized_page = max(page, 1)
        normalized_page_size = min(max(page_size, 1), MAX_PAGE_SIZE)
        return self._repository.list_for_company(
            current_user.company_id,
            page=normalized_page,
            page_size=normalized_page_size,
            active=active,
            search=search,
        )

    def get_trailer(self, current_user: User, trailer_id: uuid.UUID) -> Trailer:
        """Return a trailer in the current company."""
        trailer = self._repository.get_by_id_for_company(
            trailer_id,
            current_user.company_id,
        )
        if trailer is None:
            raise NotFoundError(code="TRAILER_NOT_FOUND", message="Trailer not found.")
        ensure_same_company(trailer.company_id, current_user)
        return trailer

    def create_trailer(
        self,
        current_user: User,
        payload: TrailerCreateRequest,
    ) -> Trailer:
        """Create a trailer in the current company."""
        validate_trailer_capacity(payload.maximum_vehicle_count)
        existing = self._repository.get_by_registration_for_company(
            payload.registration_number,
            current_user.company_id,
        )
        if existing is not None:
            raise ValidationError(
                code="REGISTRATION_ALREADY_EXISTS",
                message="A trailer with this registration number already exists.",
            )
        return self._repository.create(
            company_id=current_user.company_id,
            payload=payload,
            created_by=current_user.id,
        )

    def update_trailer(
        self,
        current_user: User,
        trailer_id: uuid.UUID,
        payload: TrailerUpdateRequest,
    ) -> Trailer:
        """Update a trailer in the current company."""
        validate_trailer_capacity(payload.maximum_vehicle_count)
        trailer = self.get_trailer(current_user, trailer_id)
        if payload.registration_number.upper() != trailer.registration_number:
            existing = self._repository.get_by_registration_for_company(
                payload.registration_number,
                current_user.company_id,
            )
            if existing is not None and existing.id != trailer.id:
                raise ValidationError(
                    code="REGISTRATION_ALREADY_EXISTS",
                    message="A trailer with this registration number already exists.",
                )
        return self._repository.update(trailer, payload, current_user.id)

    def delete_trailer(self, current_user: User, trailer_id: uuid.UUID) -> None:
        """Soft delete a trailer in the current company."""
        trailer = self.get_trailer(current_user, trailer_id)
        self._repository.soft_delete(trailer, current_user.id)
