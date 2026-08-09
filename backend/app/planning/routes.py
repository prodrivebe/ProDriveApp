"""Planning API routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.orders.permissions import require_order_manager
from app.planning.planning_service import PlanningService
from app.planning.schemas import (
    LoadPlanRequest,
    LoadPlanResponse,
    OptimizationResponse,
    PlanningAssignRequest,
    PlanningBoardQuery,
    PlanningBoardResponse,
    OptimizeRequest,
    ValidateRequest,
    ValidationResponse,
)
from app.common.responses import SuccessResponse, success_response
from app.users.models import User

router = APIRouter(prefix="/planning", tags=["Planning"])


def get_planning_service(db: Session = Depends(get_db)) -> PlanningService:
    return PlanningService(db)


@router.get("/board", response_model=SuccessResponse[PlanningBoardResponse])
def get_planning_board(
    search: str | None = Query(default=None),
    planned_date: str | None = Query(default=None),
    driver_id: uuid.UUID | None = Query(default=None),
    truck_id: uuid.UUID | None = Query(default=None),
    trailer_id: uuid.UUID | None = Query(default=None),
    current_user: User = Depends(require_order_manager),
    planning_service: PlanningService = Depends(get_planning_service),
) -> SuccessResponse[PlanningBoardResponse]:
    from datetime import date as date_type

    query = PlanningBoardQuery(
        search=search,
        planned_date=date_type.fromisoformat(planned_date) if planned_date else None,
        driver_id=driver_id,
        truck_id=truck_id,
        trailer_id=trailer_id,
    )
    return success_response(planning_service.get_board(current_user, query))


@router.post("/assign", response_model=SuccessResponse[dict[str, object]])
def planning_assign(
    payload: PlanningAssignRequest,
    request: Request,
    current_user: User = Depends(require_order_manager),
    planning_service: PlanningService = Depends(get_planning_service),
) -> SuccessResponse[dict[str, object]]:
    ip_address = request.client.host if request.client else None
    order = planning_service.assign(current_user, payload, ip_address=ip_address)
    return success_response(
        {
            "id": str(order.id),
            "order_number": order.order_number,
            "status": order.status,
            "assigned_driver_id": str(order.assigned_driver_id) if order.assigned_driver_id else None,
            "assigned_truck_id": str(order.assigned_truck_id) if order.assigned_truck_id else None,
            "assigned_trailer_id": str(order.assigned_trailer_id) if order.assigned_trailer_id else None,
        }
    )


@router.post("/load-plan", response_model=SuccessResponse[LoadPlanResponse])
def save_load_plan(
    payload: LoadPlanRequest,
    request: Request,
    current_user: User = Depends(require_order_manager),
    planning_service: PlanningService = Depends(get_planning_service),
) -> SuccessResponse[LoadPlanResponse]:
    ip_address = request.client.host if request.client else None
    return success_response(
        planning_service.save_load_plan(current_user, payload, ip_address=ip_address)
    )


@router.get("/load-plan/{order_id}", response_model=SuccessResponse[LoadPlanResponse])
def get_load_plan(
    order_id: uuid.UUID,
    current_user: User = Depends(require_order_manager),
    planning_service: PlanningService = Depends(get_planning_service),
) -> SuccessResponse[LoadPlanResponse]:
    return success_response(planning_service.get_load_plan(current_user, order_id))


@router.post("/optimize", response_model=SuccessResponse[OptimizationResponse])
def optimize_plan(
    payload: OptimizeRequest,
    current_user: User = Depends(require_order_manager),
    planning_service: PlanningService = Depends(get_planning_service),
) -> SuccessResponse[OptimizationResponse]:
    return success_response(
        planning_service.optimize(
            current_user,
            payload.order_id,
            include_route=payload.include_route,
        )
    )


@router.post("/validate", response_model=SuccessResponse[ValidationResponse])
def validate_plan(
    payload: ValidateRequest,
    current_user: User = Depends(require_order_manager),
    planning_service: PlanningService = Depends(get_planning_service),
) -> SuccessResponse[ValidationResponse]:
    return success_response(planning_service.validate_plan(current_user, payload))
