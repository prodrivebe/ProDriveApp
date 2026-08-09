"""REST endpoints for realtime presence."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.auth.dependencies import get_current_user
from app.common.responses import SuccessResponse, success_response
from app.realtime.event_service import get_event_service
from app.users.models import User

router = APIRouter(prefix="/realtime", tags=["realtime"])


@router.get("/presence", response_model=SuccessResponse[list[dict[str, object]]])
def list_presence(
    current_user: User = Depends(get_current_user),
) -> SuccessResponse[list[dict[str, object]]]:
    """Return online users for the current company."""
    service = get_event_service()
    if service is None:
        return success_response([])
    records = service._presence.list_company_presence(current_user.company_id)
    return success_response(records)
