"""Company API routes."""

from fastapi import APIRouter, Depends, File, Request, UploadFile
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.permissions import require_roles
from app.common.enums import UserRole
from app.common.responses import SuccessResponse, success_response
from app.companies.permissions import require_company_admin, require_company_reader
from app.companies.schemas import (
    CompanyLogoResponse,
    CompanyResponse,
    CompanySettingsResponse,
    CompanySettingsUpdateRequest,
    CompanyUpdateRequest,
)
from app.companies.service import CompanyService
from app.config.settings import Settings, get_settings
from app.database.session import get_db
from app.users.models import User

router = APIRouter(prefix="/companies", tags=["Companies"])


def get_client_ip(request: Request) -> str | None:
    """Extract the client IP address from the request."""
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    if request.client is not None:
        return request.client.host
    return None


def get_company_service(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> CompanyService:
    """Provide a company service instance."""
    return CompanyService(db, settings)


@router.get("/me", response_model=SuccessResponse[CompanyResponse])
def get_my_company(
    current_user: User = Depends(require_company_reader),
    company_service: CompanyService = Depends(get_company_service),
) -> SuccessResponse[CompanyResponse]:
    """Return the authenticated user's company profile."""
    company = company_service.get_my_company(current_user)
    return success_response(CompanyResponse.model_validate(company))


@router.put("/me", response_model=SuccessResponse[CompanyResponse])
def update_my_company(
    payload: CompanyUpdateRequest,
    request: Request,
    current_user: User = Depends(require_company_admin),
    company_service: CompanyService = Depends(get_company_service),
) -> SuccessResponse[CompanyResponse]:
    """Update the authenticated user's company profile."""
    company = company_service.update_my_company(
        current_user,
        payload,
        get_client_ip(request),
    )
    return success_response(CompanyResponse.model_validate(company))


@router.post("/me/logo", response_model=SuccessResponse[CompanyLogoResponse])
def upload_company_logo(
    request: Request,
    logo: UploadFile = File(...),
    current_user: User = Depends(require_company_admin),
    company_service: CompanyService = Depends(get_company_service),
) -> SuccessResponse[CompanyLogoResponse]:
    """Upload a company logo image."""
    logo_url = company_service.upload_company_logo(
        current_user,
        logo,
        get_client_ip(request),
    )
    return success_response(CompanyLogoResponse(logo_url=logo_url))


@router.get("/settings", response_model=SuccessResponse[CompanySettingsResponse])
def get_company_settings(
    current_user: User = Depends(require_company_reader),
    company_service: CompanyService = Depends(get_company_service),
) -> SuccessResponse[CompanySettingsResponse]:
    """Return company operational settings and branding."""
    settings = company_service.get_company_settings(current_user)
    return success_response(CompanySettingsResponse.model_validate(settings))


@router.put("/settings", response_model=SuccessResponse[CompanySettingsResponse])
def update_company_settings(
    payload: CompanySettingsUpdateRequest,
    request: Request,
    current_user: User = Depends(require_company_admin),
    company_service: CompanyService = Depends(get_company_service),
) -> SuccessResponse[CompanySettingsResponse]:
    """Update company operational settings and branding."""
    settings = company_service.update_company_settings(
        current_user,
        payload,
        get_client_ip(request),
    )
    return success_response(CompanySettingsResponse.model_validate(settings))
