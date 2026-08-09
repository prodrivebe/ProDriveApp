"""Planning persistence layer."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session, joinedload

from app.common.enums import LoadingPlanStatus
from app.planning.models.loading_plan import LoadingPlan, LoadingPosition


class LoadingPlanRepository:
    """Database access for loading plans."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_order_for_company(
        self,
        order_id: uuid.UUID,
        company_id: uuid.UUID,
    ) -> LoadingPlan | None:
        return (
            self._db.query(LoadingPlan)
            .options(joinedload(LoadingPlan.positions))
            .filter(
                LoadingPlan.order_id == order_id,
                LoadingPlan.company_id == company_id,
            )
            .order_by(LoadingPlan.created_at.desc())
            .first()
        )

    def get_by_id_for_company(
        self,
        plan_id: uuid.UUID,
        company_id: uuid.UUID,
    ) -> LoadingPlan | None:
        return (
            self._db.query(LoadingPlan)
            .options(joinedload(LoadingPlan.positions))
            .filter(
                LoadingPlan.id == plan_id,
                LoadingPlan.company_id == company_id,
            )
            .one_or_none()
        )

    def create(
        self,
        *,
        company_id: uuid.UUID,
        order_id: uuid.UUID,
        trailer_id: uuid.UUID | None,
        status: LoadingPlanStatus,
        route_sequence_json: dict[str, object] | None,
        estimated_total_height: float | None,
        estimated_total_weight: float | None,
        estimated_travel_km: float | None,
        front_axle_percent: float | None,
        rear_axle_percent: float | None,
        validation_warnings: list[str] | None,
        ai_generated: bool,
        created_by: uuid.UUID,
    ) -> LoadingPlan:
        plan = LoadingPlan(
            company_id=company_id,
            order_id=order_id,
            trailer_id=trailer_id,
            status=status.value,
            route_sequence_json=json.dumps(route_sequence_json) if route_sequence_json else None,
            estimated_total_height=estimated_total_height,
            estimated_total_weight=estimated_total_weight,
            estimated_travel_km=estimated_travel_km,
            front_axle_percent=front_axle_percent,
            rear_axle_percent=rear_axle_percent,
            validation_warnings_json=json.dumps(validation_warnings or []),
            ai_generated=ai_generated,
            created_by=created_by,
            updated_by=created_by,
            created_at=datetime.now(tz=UTC),
            updated_at=datetime.now(tz=UTC),
        )
        self._db.add(plan)
        self._db.commit()
        self._db.refresh(plan)
        refreshed = self.get_by_id_for_company(plan.id, plan.company_id)
        return refreshed if refreshed is not None else plan

    def replace_positions(
        self,
        plan: LoadingPlan,
        positions: list[dict[str, object]],
        *,
        confirmed: bool,
        updated_by: uuid.UUID,
    ) -> LoadingPlan:
        self._db.query(LoadingPosition).filter(
            LoadingPosition.loading_plan_id == plan.id
        ).delete()
        for item in positions:
            self._db.add(
                LoadingPosition(
                    company_id=plan.company_id,
                    loading_plan_id=plan.id,
                    vehicle_id=uuid.UUID(str(item["vehicle_id"])),
                    upper_deck=bool(item.get("upper_deck", False)),
                    trailer_position=int(item["trailer_position"]),
                    loading_order=int(item["loading_order"]),
                    unloading_order=int(item["unloading_order"]),
                    destination_city=item.get("destination_city"),
                    confirmed_by_dispatcher=confirmed,
                    ai_generated=bool(item.get("ai_generated", False)),
                )
            )
        plan.updated_by = updated_by
        plan.updated_at = datetime.now(tz=UTC)
        if confirmed:
            plan.status = LoadingPlanStatus.CONFIRMED.value
            plan.confirmed_by = updated_by
            plan.confirmed_at = datetime.now(tz=UTC)
        self._db.add(plan)
        self._db.commit()
        self._db.refresh(plan)
        refreshed = self.get_by_id_for_company(plan.id, plan.company_id)
        return refreshed if refreshed is not None else plan
