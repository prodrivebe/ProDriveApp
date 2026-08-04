"""Company persistence layer."""

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.companies.models import Company, CompanySettings
from app.companies.schemas import CompanySettingsUpdateRequest, CompanyUpdateRequest


class CompanyRepository:
    """Repository for tenant company records."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def get_by_id_for_company(self, company_id: uuid.UUID) -> Company | None:
        """Return a company scoped to the tenant identifier."""
        statement = select(Company).where(Company.id == company_id)
        return self._db.scalar(statement)

    def update_company(
        self,
        company: Company,
        payload: CompanyUpdateRequest,
    ) -> Company:
        """Update company profile fields."""
        company.name = payload.name
        company.vat_number = payload.vat_number
        company.address = payload.address
        company.country = payload.country
        company.phone = payload.phone
        company.email = str(payload.email) if payload.email is not None else None
        company.subscription_plan = payload.subscription_plan
        self._db.add(company)
        self._db.commit()
        self._db.refresh(company)
        return company

    def update_logo(self, company: Company, logo_url: str) -> Company:
        """Update the company logo reference."""
        company.logo_url = logo_url
        self._db.add(company)
        self._db.commit()
        self._db.refresh(company)
        return company

    def get_settings_for_company(self, company_id: uuid.UUID) -> CompanySettings | None:
        """Return settings for a tenant company."""
        statement = select(CompanySettings).where(CompanySettings.company_id == company_id)
        return self._db.scalar(statement)

    def create_default_settings(self, company_id: uuid.UUID) -> CompanySettings:
        """Create default settings for a company."""
        settings = CompanySettings(company_id=company_id)
        self._db.add(settings)
        self._db.commit()
        self._db.refresh(settings)
        return settings

    def update_settings(
        self,
        settings: CompanySettings,
        payload: CompanySettingsUpdateRequest,
    ) -> CompanySettings:
        """Update company settings and branding."""
        settings.timezone = payload.timezone
        settings.default_currency = payload.default_currency.upper()
        settings.order_number_prefix = payload.order_number_prefix
        settings.require_vehicle_photos = payload.require_vehicle_photos
        settings.primary_color = payload.primary_color.upper()
        settings.secondary_color = payload.secondary_color.upper()
        settings.accent_color = payload.accent_color.upper()
        settings.dashboard_title = payload.dashboard_title
        self._db.add(settings)
        self._db.commit()
        self._db.refresh(settings)
        return settings
