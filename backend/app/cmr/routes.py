"""CMR API routes."""

import uuid

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from app.common.responses import SuccessResponse, success_response
from app.cmr.service import CmrService
from app.config.settings import Settings, get_settings
from app.database.session import get_db
from app.documents.schemas import DocumentResponse
from app.orders.permissions import require_order_actor, require_order_manager
from app.users.models import User

router = APIRouter(prefix="/orders", tags=["CMR"])


def get_cmr_service(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> CmrService:
    """Provide a CMR service instance."""
    return CmrService(db, settings)


@router.post("/{order_id}/cmr/generate", response_model=SuccessResponse[DocumentResponse])
def generate_cmr(
    order_id: uuid.UUID,
    current_user: User = Depends(require_order_actor),
    cmr_service: CmrService = Depends(get_cmr_service),
) -> SuccessResponse[DocumentResponse]:
    """Generate a CMR document for an order."""
    document = cmr_service.generate_cmr(current_user, order_id)
    return success_response(DocumentResponse.model_validate(document))


@router.get("/{order_id}/cmr", response_model=SuccessResponse[DocumentResponse])
def get_cmr(
    order_id: uuid.UUID,
    current_user: User = Depends(require_order_actor),
    cmr_service: CmrService = Depends(get_cmr_service),
) -> SuccessResponse[DocumentResponse]:
    """Return the latest generated CMR for an order."""
    document = cmr_service.get_cmr(current_user, order_id)
    return success_response(DocumentResponse.model_validate(document))


@router.post(
    "/{order_id}/cmr/upload",
    response_model=SuccessResponse[DocumentResponse],
    status_code=201,
)
def upload_signed_cmr(
    order_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(require_order_actor),
    cmr_service: CmrService = Depends(get_cmr_service),
) -> SuccessResponse[DocumentResponse]:
    """Upload a signed CMR copy."""
    document = cmr_service.upload_signed_cmr(current_user, order_id, file)
    return success_response(DocumentResponse.model_validate(document))
