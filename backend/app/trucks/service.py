"""Truck business logic."""

import uuid

from sqlalchemy.orm import Session

from app.common.exceptions import NotFoundError, ValidationError
from app.common.tenant import ensure_same_company
from app.trucks.models import Truck
from app.trucks.repository import TruckRepository
from app.trucks.schemas import TruckCreateRequest, TruckUpdateRequest
from app.users.models import User

MAX_PAGE_SIZE = 100


class TruckService:
    """Truck management workflows."""

    def __init__(self, db: Session) -> None:
        self._db = db
        self._repository = TruckRepository(db)

    def list_trucks(
        self,
        current_user: User,
        *,
        page: int,
        page_size: int,
        active: bool | None,
        search: str | None,
    ) -> tuple[list[Truck], int]:
        """List trucks for the current company."""
        normalized_page = max(page, 1)
        normalized_page_size = min(max(page_size, 1), MAX_PAGE_SIZE)
        return self._repository.list_for_company(
            current_user.company_id,
            page=normalized_page,
            page_size=normalized_page_size,
            active=active,
            search=search,
        )

    def get_truck(self, current_user: User, truck_id: uuid.UUID) -> Truck:
        """Return a truck in the current company."""
        truck = self._repository.get_by_id_for_company(truck_id, current_user.company_id)
        if truck is None:
            raise NotFoundError(code="TRUCK_NOT_FOUND", message="Truck not found.")
        ensure_same_company(truck.company_id, current_user)
        return truck

    def create_truck(self, current_user: User, payload: TruckCreateRequest) -> Truck:
        """Create a truck in the current company."""
        existing = self._repository.get_by_registration_for_company(
            payload.registration_number,
            current_user.company_id,
        )
        if existing is not None:
            raise ValidationError(
                code="REGISTRATION_ALREADY_EXISTS",
                message="A truck with this registration number already exists.",
            )
        return self._repository.create(
            company_id=current_user.company_id,
            payload=payload,
            created_by=current_user.id,
        )

    def update_truck(
        self,
        current_user: User,
        truck_id: uuid.UUID,
        payload: TruckUpdateRequest,
    ) -> Truck:
        """Update a truck in the current company."""
        truck = self.get_truck(current_user, truck_id)
        if payload.registration_number.upper() != truck.registration_number:
            existing = self._repository.get_by_registration_for_company(
                payload.registration_number,
                current_user.company_id,
            )
            if existing is not None and existing.id != truck.id:
                raise ValidationError(
                    code="REGISTRATION_ALREADY_EXISTS",
                    message="A truck with this registration number already exists.",
                )
        return self._repository.update(truck, payload, current_user.id)

    def delete_truck(self, current_user: User, truck_id: uuid.UUID) -> None:
        """Soft delete a truck in the current company."""
        truck = self.get_truck(current_user, truck_id)
        self._repository.soft_delete(truck, current_user.id)
