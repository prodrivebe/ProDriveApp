"""Company business logic."""

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.audit.service import AuditService
from app.common.exceptions import NotFoundError
from app.common.storage.local import LocalFileStorage
from app.common.tenant import ensure_same_company
from app.companies.models import Company, CompanySettings
from app.companies.repository import CompanyRepository
from app.companies.schemas import CompanySettingsUpdateRequest, CompanyUpdateRequest
from app.config.settings import Settings
from app.users.models import User


class CompanyService:
    """Company profile, settings, and branding workflows."""

    def __init__(self, db: Session, settings: Settings) -> None:
        self._db = db
        self._settings = settings
        self._repository = CompanyRepository(db)
        self._audit_service = AuditService(db)
        self._storage = LocalFileStorage(settings)

    def get_my_company(self, current_user: User) -> Company:
        """Return the authenticated user's company."""
        company = self._repository.get_by_id_for_company(current_user.company_id)
        if company is None:
            raise NotFoundError(
                code="COMPANY_NOT_FOUND",
                message="Company not found.",
            )
        return company

    def update_my_company(
        self,
        current_user: User,
        payload: CompanyUpdateRequest,
        ip_address: str | None,
    ) -> Company:
        """Update the authenticated user's company profile."""
        company = self.get_my_company(current_user)
        ensure_same_company(company.id, current_user)
        updated_company = self._repository.update_company(company, payload)
        self._audit_service.record_company_updated(
            company_id=company.id,
            user_id=current_user.id,
            ip_address=ip_address,
            entity_id=str(company.id),
        )
        return updated_company

    def get_company_settings(self, current_user: User) -> CompanySettings:
        """Return settings for the authenticated user's company."""
        settings = self._repository.get_settings_for_company(current_user.company_id)
        if settings is None:
            settings = self._repository.create_default_settings(current_user.company_id)
        ensure_same_company(settings.company_id, current_user)
        return settings

    def update_company_settings(
        self,
        current_user: User,
        payload: CompanySettingsUpdateRequest,
        ip_address: str | None,
    ) -> CompanySettings:
        """Update settings and branding for the authenticated user's company."""
        settings = self.get_company_settings(current_user)
        updated_settings = self._repository.update_settings(settings, payload)
        self._audit_service.record_company_settings_updated(
            company_id=current_user.company_id,
            user_id=current_user.id,
            ip_address=ip_address,
            entity_id=str(settings.id),
        )
        return updated_settings

    def upload_company_logo(
        self,
        current_user: User,
        upload_file: UploadFile,
        ip_address: str | None,
    ) -> str:
        """Upload and store a company logo."""
        company = self.get_my_company(current_user)
        logo_url = self._storage.save_company_logo(
            company_id=company.id,
            upload_file=upload_file,
        )
        self._repository.update_logo(company, logo_url)
        self._audit_service.record_company_logo_updated(
            company_id=company.id,
            user_id=current_user.id,
            ip_address=ip_address,
            entity_id=str(company.id),
        )
        return logo_url
