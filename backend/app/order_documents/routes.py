"""Order document API routes."""

import uuid

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from sqlalchemy.orm import Session

from app.common.enums import OrderDocumentType
from app.common.responses import SuccessResponse, success_response
from app.config.settings import Settings, get_settings
from app.database.session import get_db
from app.order_documents.permissions import require_document_actor, require_document_manager
from app.order_documents.schemas import OrderDocumentResponse
from app.order_documents.service import OrderDocumentService
from app.users.models import User

router = APIRouter(prefix="/orders", tags=["Order Documents"])
document_router = APIRouter(prefix="/documents", tags=["Order Documents"])


def get_client_ip(request: Request) -> str | None:
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip()
    if request.client is not None:
        return request.client.host
    return None


def get_document_service(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> OrderDocumentService:
    return OrderDocumentService(db, settings)


@router.post(
    "/{order_id}/documents",
    response_model=SuccessResponse[OrderDocumentResponse],
    status_code=201,
)
def upload_order_document(
    order_id: uuid.UUID,
    request: Request,
    file: UploadFile = File(...),
    document_type: OrderDocumentType = Form(default=OrderDocumentType.CMR),
    current_user: User = Depends(require_document_actor),
    document_service: OrderDocumentService = Depends(get_document_service),
) -> SuccessResponse[OrderDocumentResponse]:
    document = document_service.upload_document(
        current_user,
        order_id,
        file,
        document_type=document_type,
        ip_address=get_client_ip(request),
    )
    return success_response(OrderDocumentResponse.model_validate(document))


@router.get(
    "/{order_id}/documents",
    response_model=SuccessResponse[list[OrderDocumentResponse]],
)
def list_order_documents(
    order_id: uuid.UUID,
    current_user: User = Depends(require_document_actor),
    document_service: OrderDocumentService = Depends(get_document_service),
) -> SuccessResponse[list[OrderDocumentResponse]]:
    documents = document_service.list_documents(current_user, order_id)
    return success_response(
        [OrderDocumentResponse.model_validate(document) for document in documents]
    )


@document_router.get("/{document_id}", response_model=SuccessResponse[OrderDocumentResponse])
def get_order_document(
    document_id: uuid.UUID,
    current_user: User = Depends(require_document_actor),
    document_service: OrderDocumentService = Depends(get_document_service),
) -> SuccessResponse[OrderDocumentResponse]:
    document = document_service.get_document(current_user, document_id)
    return success_response(OrderDocumentResponse.model_validate(document))


@document_router.delete("/{document_id}", response_model=SuccessResponse[dict[str, str]])
def delete_order_document(
    document_id: uuid.UUID,
    current_user: User = Depends(require_document_manager),
    document_service: OrderDocumentService = Depends(get_document_service),
) -> SuccessResponse[dict[str, str]]:
    document_service.delete_document(current_user, document_id)
    return success_response({"message": "Document deleted successfully."})
