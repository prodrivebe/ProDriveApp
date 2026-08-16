"""CMR API routes."""

import uuid

from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.cmr.service import CmrService
from app.common.responses import SuccessResponse, success_response
from app.config.settings import Settings, get_settings
from app.database.session import get_db
from app.order_documents.schemas import CmrSignRequest, CmrSignResponse, OrderDocumentResponse
from app.order_stops.schemas import OrderStopResponse
from app.orders.permissions import require_order_actor
from app.orders.schemas import OrderResponse
from app.users.models import User

router = APIRouter(prefix="/orders", tags=["CMR"])


def get_client_ip(request: Request) -> str | None:
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip()
    if request.client is not None:
        return request.client.host
    return None


def get_cmr_service(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> CmrService:
    """Provide a CMR service instance."""
    return CmrService(db, settings)


@router.get("/{order_id}/cmr/preview")
def preview_cmr_pdf(
    order_id: uuid.UUID,
    current_user: User = Depends(require_order_actor),
    cmr_service: CmrService = Depends(get_cmr_service),
) -> Response:
    """Generate and return a draft CMR PDF for driver review."""
    pdf_bytes = cmr_service.generate_preview_pdf(current_user, order_id)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="cmr-{order_id}-preview.pdf"'},
    )


@router.post("/{order_id}/cmr/generate", response_model=SuccessResponse[OrderDocumentResponse])
def generate_cmr(
    order_id: uuid.UUID,
    current_user: User = Depends(require_order_actor),
    cmr_service: CmrService = Depends(get_cmr_service),
) -> SuccessResponse[OrderDocumentResponse]:
    """Generate a draft CMR PDF for an order during pickup loading."""
    document = cmr_service.generate_draft(current_user, order_id)
    return success_response(OrderDocumentResponse.model_validate(document))


@router.post("/{order_id}/cmr/sign", response_model=SuccessResponse[CmrSignResponse])
def sign_cmr(
    order_id: uuid.UUID,
    payload: CmrSignRequest,
    request: Request,
    current_user: User = Depends(require_order_actor),
    cmr_service: CmrService = Depends(get_cmr_service),
) -> SuccessResponse[CmrSignResponse]:
    """Sign, stamp, and lock the CMR; confirm delivery workflow step."""
    document, updated_order, updated_stop = cmr_service.sign_and_finalize(
        current_user,
        order_id,
        payload.signature_png_base64,
        ip_address=get_client_ip(request),
    )
    return success_response(
        CmrSignResponse(
            document=OrderDocumentResponse.model_validate(document),
            order=OrderResponse.model_validate(updated_order),
            stop=(
                OrderStopResponse.model_validate(updated_stop)
                if updated_stop is not None
                else None
            ),
        )
    )


@router.get("/{order_id}/cmr", response_model=SuccessResponse[OrderDocumentResponse])
def get_cmr(
    order_id: uuid.UUID,
    current_user: User = Depends(require_order_actor),
    cmr_service: CmrService = Depends(get_cmr_service),
) -> SuccessResponse[OrderDocumentResponse]:
    """Return the latest CMR document for an order."""
    document = cmr_service.get_latest_cmr(current_user, order_id)
    return success_response(OrderDocumentResponse.model_validate(document))
