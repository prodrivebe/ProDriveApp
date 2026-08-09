"""VIN verification persistence layer."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.enums import VinVerificationAction
from app.vin_verification.models import VinVerificationHistory


class VinVerificationRepository:
    """Repository for VIN verification history."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def list_for_vehicle(
        self,
        vehicle_id: uuid.UUID,
        company_id: uuid.UUID,
    ) -> list[VinVerificationHistory]:
        """Return VIN history newest first."""
        statement = (
            select(VinVerificationHistory)
            .where(
                VinVerificationHistory.vehicle_id == vehicle_id,
                VinVerificationHistory.company_id == company_id,
            )
            .order_by(VinVerificationHistory.verified_at.desc())
        )
        return list(self._db.scalars(statement).all())

    def create(
        self,
        *,
        company_id: uuid.UUID,
        order_id: uuid.UUID,
        vehicle_id: uuid.UUID,
        original_vin: str | None,
        verified_vin: str,
        action: VinVerificationAction,
        verified_by: uuid.UUID,
    ) -> VinVerificationHistory:
        """Append an immutable VIN history record."""
        entry = VinVerificationHistory(
            company_id=company_id,
            order_id=order_id,
            vehicle_id=vehicle_id,
            original_vin=original_vin,
            verified_vin=verified_vin,
            action=action,
            verified_by=verified_by,
            verified_at=datetime.now(tz=UTC),
        )
        self._db.add(entry)
        self._db.commit()
        self._db.refresh(entry)
        return entry
