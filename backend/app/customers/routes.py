"""Customer API routes."""

import uuid

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.orm import Session

from app.common.pagination import build_list_meta
from app.common.responses import SuccessResponse, success_response
from app.customers.permissions import require_customer_manager
from app.customers.schemas import (
    CustomerContactCreateRequest,
    CustomerContactResponse,
    CustomerContactUpdateRequest,
    CustomerCreateRequest,
    CustomerResponse,
    CustomerUpdateRequest,
)
from app.customers.service import CustomerService
from app.database.session import get_db
from app.orders.schemas import OrderSummaryResponse
from app.users.models import User

router = APIRouter(prefix="/customers", tags=["Customers"])


def get_client_ip(request: Request) -> str | None:
    """Extract the client IP address from the request."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    if request.client is not None:
        return request.client.host
    return None


def get_customer_service(db: Session = Depends(get_db)) -> CustomerService:
    """Provide a customer service instance."""
    return CustomerService(db)


@router.get("", response_model=SuccessResponse[list[CustomerResponse]])
def list_customers(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    search: str | None = Query(default=None),
    current_user: User = Depends(require_customer_manager),
    customer_service: CustomerService = Depends(get_customer_service),
) -> SuccessResponse[list[CustomerResponse]]:
    """List customers for the current company."""
    customers, total = customer_service.list_customers(
        current_user,
        page=page,
        page_size=page_size,
        search=search,
    )
    data = [CustomerResponse.model_validate(customer) for customer in customers]
    return success_response(data, meta=build_list_meta(page, page_size, total))


@router.post("", response_model=SuccessResponse[CustomerResponse], status_code=201)
def create_customer(
    payload: CustomerCreateRequest,
    request: Request,
    current_user: User = Depends(require_customer_manager),
    customer_service: CustomerService = Depends(get_customer_service),
) -> SuccessResponse[CustomerResponse]:
    """Create a customer."""
    customer = customer_service.create_customer(
        current_user,
        payload,
        get_client_ip(request),
    )
    return success_response(CustomerResponse.model_validate(customer))


@router.get("/{customer_id}", response_model=SuccessResponse[CustomerResponse])
def get_customer(
    customer_id: uuid.UUID,
    current_user: User = Depends(require_customer_manager),
    customer_service: CustomerService = Depends(get_customer_service),
) -> SuccessResponse[CustomerResponse]:
    """Return a customer."""
    customer = customer_service.get_customer(current_user, customer_id)
    return success_response(CustomerResponse.model_validate(customer))


@router.put("/{customer_id}", response_model=SuccessResponse[CustomerResponse])
def update_customer(
    customer_id: uuid.UUID,
    payload: CustomerUpdateRequest,
    request: Request,
    current_user: User = Depends(require_customer_manager),
    customer_service: CustomerService = Depends(get_customer_service),
) -> SuccessResponse[CustomerResponse]:
    """Update a customer."""
    customer = customer_service.update_customer(
        current_user,
        customer_id,
        payload,
        get_client_ip(request),
    )
    return success_response(CustomerResponse.model_validate(customer))


@router.delete("/{customer_id}", response_model=SuccessResponse[dict[str, str]])
def delete_customer(
    customer_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(require_customer_manager),
    customer_service: CustomerService = Depends(get_customer_service),
) -> SuccessResponse[dict[str, str]]:
    """Soft delete a customer."""
    customer_service.delete_customer(
        current_user,
        customer_id,
        get_client_ip(request),
    )
    return success_response({"message": "Customer deleted successfully."})


@router.get(
    "/{customer_id}/contacts",
    response_model=SuccessResponse[list[CustomerContactResponse]],
)
def list_customer_contacts(
    customer_id: uuid.UUID,
    current_user: User = Depends(require_customer_manager),
    customer_service: CustomerService = Depends(get_customer_service),
) -> SuccessResponse[list[CustomerContactResponse]]:
    """List contacts for a customer."""
    contacts = customer_service.list_customer_contacts(current_user, customer_id)
    data = [CustomerContactResponse.model_validate(contact) for contact in contacts]
    return success_response(data)


@router.post(
    "/{customer_id}/contacts",
    response_model=SuccessResponse[CustomerContactResponse],
    status_code=201,
)
def create_customer_contact(
    customer_id: uuid.UUID,
    payload: CustomerContactCreateRequest,
    request: Request,
    current_user: User = Depends(require_customer_manager),
    customer_service: CustomerService = Depends(get_customer_service),
) -> SuccessResponse[CustomerContactResponse]:
    """Create a contact for a customer."""
    contact = customer_service.create_customer_contact(
        current_user,
        customer_id,
        payload,
        get_client_ip(request),
    )
    return success_response(CustomerContactResponse.model_validate(contact))


@router.put(
    "/{customer_id}/contacts/{contact_id}",
    response_model=SuccessResponse[CustomerContactResponse],
)
def update_customer_contact(
    customer_id: uuid.UUID,
    contact_id: uuid.UUID,
    payload: CustomerContactUpdateRequest,
    request: Request,
    current_user: User = Depends(require_customer_manager),
    customer_service: CustomerService = Depends(get_customer_service),
) -> SuccessResponse[CustomerContactResponse]:
    """Update a customer contact."""
    contact = customer_service.update_customer_contact(
        current_user,
        customer_id,
        contact_id,
        payload,
        get_client_ip(request),
    )
    return success_response(CustomerContactResponse.model_validate(contact))


@router.delete(
    "/{customer_id}/contacts/{contact_id}",
    response_model=SuccessResponse[dict[str, str]],
)
def delete_customer_contact(
    customer_id: uuid.UUID,
    contact_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(require_customer_manager),
    customer_service: CustomerService = Depends(get_customer_service),
) -> SuccessResponse[dict[str, str]]:
    """Soft delete a customer contact."""
    customer_service.delete_customer_contact(
        current_user,
        customer_id,
        contact_id,
        get_client_ip(request),
    )
    return success_response({"message": "Customer contact deleted successfully."})


@router.get(
    "/{customer_id}/history",
    response_model=SuccessResponse[list[OrderSummaryResponse]],
)
def list_customer_history(
    customer_id: uuid.UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    current_user: User = Depends(require_customer_manager),
    customer_service: CustomerService = Depends(get_customer_service),
) -> SuccessResponse[list[OrderSummaryResponse]]:
    """List customer order history."""
    history, total = customer_service.list_customer_history(current_user, customer_id)
    return success_response(history, meta=build_list_meta(page, page_size, total))
