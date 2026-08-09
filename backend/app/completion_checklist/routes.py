"""Completion checklist API routes."""

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.responses import SuccessResponse, success_response
from app.completion_checklist.permissions import require_checklist_actor
from app.completion_checklist.schemas import (
    CompletionChecklistResponse,
    CompletionValidationResponse,
)
from app.completion_checklist.service import CompletionChecklistService
from app.database.session import get_db
from app.users.models import User

router = APIRouter(prefix="/orders", tags=["Completion Checklist"])


def get_checklist_service(db: Session = Depends(get_db)) -> CompletionChecklistService:
    return CompletionChecklistService(db)


@router.get(
    "/{order_id}/completion-checklist",
    response_model=SuccessResponse[CompletionChecklistResponse],
)
def get_completion_checklist(
    order_id: uuid.UUID,
    current_user: User = Depends(require_checklist_actor),
    checklist_service: CompletionChecklistService = Depends(get_checklist_service),
) -> SuccessResponse[CompletionChecklistResponse]:
    checklist = checklist_service.get_checklist(current_user, order_id)
    return success_response(checklist)


@router.post(
    "/{order_id}/validate-completion",
    response_model=SuccessResponse[CompletionValidationResponse],
)
def validate_completion(
    order_id: uuid.UUID,
    current_user: User = Depends(require_checklist_actor),
    checklist_service: CompletionChecklistService = Depends(get_checklist_service),
) -> SuccessResponse[CompletionValidationResponse]:
    result = checklist_service.validate_completion(current_user, order_id)
    return success_response(result)
