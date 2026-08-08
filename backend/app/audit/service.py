"""Audit logging service."""

import uuid

from sqlalchemy.orm import Session

from app.audit.repository import AuditRepository


class AuditService:
    """Service for recording audit events."""

    def __init__(self, db: Session) -> None:
        self._repository = AuditRepository(db)

    def record_login(
        self,
        *,
        company_id: uuid.UUID,
        user_id: uuid.UUID,
        ip_address: str | None,
        success: bool,
    ) -> None:
        """Record a login attempt."""
        self._repository.create(
            company_id=company_id,
            user_id=user_id,
            entity="user",
            entity_id=str(user_id),
            action="LOGIN_SUCCESS" if success else "LOGIN_FAILED",
            new_value="success" if success else "failed",
            ip_address=ip_address,
        )

    def record_logout(
        self,
        *,
        company_id: uuid.UUID,
        user_id: uuid.UUID,
        ip_address: str | None,
    ) -> None:
        """Record a logout event."""
        self._repository.create(
            company_id=company_id,
            user_id=user_id,
            entity="user",
            entity_id=str(user_id),
            action="LOGOUT",
            ip_address=ip_address,
        )

    def record_password_reset_requested(
        self,
        *,
        company_id: uuid.UUID,
        user_id: uuid.UUID,
        ip_address: str | None,
    ) -> None:
        """Record a password reset request."""
        self._repository.create(
            company_id=company_id,
            user_id=user_id,
            entity="user",
            entity_id=str(user_id),
            action="PASSWORD_RESET_REQUESTED",
            ip_address=ip_address,
        )

    def record_password_reset_completed(
        self,
        *,
        company_id: uuid.UUID,
        user_id: uuid.UUID,
        ip_address: str | None,
    ) -> None:
        """Record a completed password reset."""
        self._repository.create(
            company_id=company_id,
            user_id=user_id,
            entity="user",
            entity_id=str(user_id),
            action="PASSWORD_RESET_COMPLETED",
            ip_address=ip_address,
        )

    def record_company_updated(
        self,
        *,
        company_id: uuid.UUID,
        user_id: uuid.UUID,
        ip_address: str | None,
        entity_id: str,
    ) -> None:
        """Record a company profile update."""
        self._repository.create(
            company_id=company_id,
            user_id=user_id,
            entity="company",
            entity_id=entity_id,
            action="COMPANY_UPDATED",
            ip_address=ip_address,
        )

    def record_company_settings_updated(
        self,
        *,
        company_id: uuid.UUID,
        user_id: uuid.UUID,
        ip_address: str | None,
        entity_id: str,
    ) -> None:
        """Record a company settings update."""
        self._repository.create(
            company_id=company_id,
            user_id=user_id,
            entity="company_settings",
            entity_id=entity_id,
            action="COMPANY_SETTINGS_UPDATED",
            ip_address=ip_address,
        )

    def record_company_logo_updated(
        self,
        *,
        company_id: uuid.UUID,
        user_id: uuid.UUID,
        ip_address: str | None,
        entity_id: str,
    ) -> None:
        """Record a company logo update."""
        self._repository.create(
            company_id=company_id,
            user_id=user_id,
            entity="company",
            entity_id=entity_id,
            action="COMPANY_LOGO_UPDATED",
            new_value="logo_updated",
            ip_address=ip_address,
        )

    def record_user_created(
        self,
        *,
        company_id: uuid.UUID,
        user_id: uuid.UUID,
        entity_id: str,
        ip_address: str | None,
    ) -> None:
        """Record user creation."""
        self._repository.create(
            company_id=company_id,
            user_id=user_id,
            entity="user",
            entity_id=entity_id,
            action="USER_CREATED",
            ip_address=ip_address,
        )

    def record_user_updated(
        self,
        *,
        company_id: uuid.UUID,
        user_id: uuid.UUID,
        entity_id: str,
        ip_address: str | None,
    ) -> None:
        """Record user update."""
        self._repository.create(
            company_id=company_id,
            user_id=user_id,
            entity="user",
            entity_id=entity_id,
            action="USER_UPDATED",
            ip_address=ip_address,
        )

    def record_user_deleted(
        self,
        *,
        company_id: uuid.UUID,
        user_id: uuid.UUID,
        entity_id: str,
        ip_address: str | None,
    ) -> None:
        """Record user soft delete."""
        self._repository.create(
            company_id=company_id,
            user_id=user_id,
            entity="user",
            entity_id=entity_id,
            action="USER_DELETED",
            ip_address=ip_address,
        )

    def record_user_profile_updated(
        self,
        *,
        company_id: uuid.UUID,
        user_id: uuid.UUID,
        entity_id: str,
        ip_address: str | None,
    ) -> None:
        """Record profile update."""
        self._repository.create(
            company_id=company_id,
            user_id=user_id,
            entity="user",
            entity_id=entity_id,
            action="USER_PROFILE_UPDATED",
            ip_address=ip_address,
        )

    def record_user_password_updated(
        self,
        *,
        company_id: uuid.UUID,
        user_id: uuid.UUID,
        entity_id: str,
        ip_address: str | None,
    ) -> None:
        """Record password update."""
        self._repository.create(
            company_id=company_id,
            user_id=user_id,
            entity="user",
            entity_id=entity_id,
            action="USER_PASSWORD_UPDATED",
            ip_address=ip_address,
        )

    def record_customer_created(
        self,
        *,
        company_id: uuid.UUID,
        user_id: uuid.UUID,
        entity_id: str,
        ip_address: str | None,
    ) -> None:
        """Record customer creation."""
        self._repository.create(
            company_id=company_id,
            user_id=user_id,
            entity="customer",
            entity_id=entity_id,
            action="CUSTOMER_CREATED",
            ip_address=ip_address,
        )

    def record_customer_updated(
        self,
        *,
        company_id: uuid.UUID,
        user_id: uuid.UUID,
        entity_id: str,
        ip_address: str | None,
    ) -> None:
        """Record customer update."""
        self._repository.create(
            company_id=company_id,
            user_id=user_id,
            entity="customer",
            entity_id=entity_id,
            action="CUSTOMER_UPDATED",
            ip_address=ip_address,
        )

    def record_customer_deleted(
        self,
        *,
        company_id: uuid.UUID,
        user_id: uuid.UUID,
        entity_id: str,
        ip_address: str | None,
    ) -> None:
        """Record customer soft delete."""
        self._repository.create(
            company_id=company_id,
            user_id=user_id,
            entity="customer",
            entity_id=entity_id,
            action="CUSTOMER_DELETED",
            ip_address=ip_address,
        )

    def record_customer_contact_created(
        self,
        *,
        company_id: uuid.UUID,
        user_id: uuid.UUID,
        entity_id: str,
        ip_address: str | None,
    ) -> None:
        """Record customer contact creation."""
        self._repository.create(
            company_id=company_id,
            user_id=user_id,
            entity="customer_contact",
            entity_id=entity_id,
            action="CUSTOMER_CONTACT_CREATED",
            ip_address=ip_address,
        )

    def record_customer_contact_updated(
        self,
        *,
        company_id: uuid.UUID,
        user_id: uuid.UUID,
        entity_id: str,
        ip_address: str | None,
    ) -> None:
        """Record customer contact update."""
        self._repository.create(
            company_id=company_id,
            user_id=user_id,
            entity="customer_contact",
            entity_id=entity_id,
            action="CUSTOMER_CONTACT_UPDATED",
            ip_address=ip_address,
        )

    def record_customer_contact_deleted(
        self,
        *,
        company_id: uuid.UUID,
        user_id: uuid.UUID,
        entity_id: str,
        ip_address: str | None,
    ) -> None:
        """Record customer contact soft delete."""
        self._repository.create(
            company_id=company_id,
            user_id=user_id,
            entity="customer_contact",
            entity_id=entity_id,
            action="CUSTOMER_CONTACT_DELETED",
            ip_address=ip_address,
        )

    def record_order_created(
        self,
        *,
        company_id: uuid.UUID,
        user_id: uuid.UUID,
        entity_id: str,
        ip_address: str | None,
    ) -> None:
        """Record order creation."""
        self._repository.create(
            company_id=company_id,
            user_id=user_id,
            entity="order",
            entity_id=entity_id,
            action="ORDER_CREATED",
            ip_address=ip_address,
        )

    def record_order_updated(
        self,
        *,
        company_id: uuid.UUID,
        user_id: uuid.UUID,
        entity_id: str,
        ip_address: str | None,
    ) -> None:
        """Record order update."""
        self._repository.create(
            company_id=company_id,
            user_id=user_id,
            entity="order",
            entity_id=entity_id,
            action="ORDER_UPDATED",
            ip_address=ip_address,
        )

    def record_order_deleted(
        self,
        *,
        company_id: uuid.UUID,
        user_id: uuid.UUID,
        entity_id: str,
        ip_address: str | None,
    ) -> None:
        """Record order soft delete."""
        self._repository.create(
            company_id=company_id,
            user_id=user_id,
            entity="order",
            entity_id=entity_id,
            action="ORDER_DELETED",
            ip_address=ip_address,
        )

    def record_order_driver_assigned(
        self,
        *,
        company_id: uuid.UUID,
        user_id: uuid.UUID,
        entity_id: str,
        ip_address: str | None,
    ) -> None:
        """Record driver assignment."""
        self._repository.create(
            company_id=company_id,
            user_id=user_id,
            entity="order",
            entity_id=entity_id,
            action="ORDER_DRIVER_ASSIGNED",
            ip_address=ip_address,
        )

    def record_order_cancelled(
        self,
        *,
        company_id: uuid.UUID,
        user_id: uuid.UUID,
        entity_id: str,
        ip_address: str | None,
    ) -> None:
        """Record order cancellation."""
        self._repository.create(
            company_id=company_id,
            user_id=user_id,
            entity="order",
            entity_id=entity_id,
            action="ORDER_CANCELLED",
            ip_address=ip_address,
        )

    def record_vehicle_vin_scanned(
        self,
        *,
        company_id: uuid.UUID,
        user_id: uuid.UUID,
        entity_id: str,
        old_value: str | None,
        new_value: str,
        ip_address: str | None,
    ) -> None:
        """Record a scanned VIN update."""
        self._repository.create(
            company_id=company_id,
            user_id=user_id,
            entity="order_vehicle",
            entity_id=entity_id,
            action="VIN_SCANNED",
            old_value=old_value,
            new_value=new_value,
            ip_address=ip_address,
        )

    def record_driver_created(
        self,
        *,
        company_id: uuid.UUID,
        user_id: uuid.UUID,
        entity_id: str,
        ip_address: str | None,
    ) -> None:
        """Record driver creation."""
        self._repository.create(
            company_id=company_id,
            user_id=user_id,
            entity="driver",
            entity_id=entity_id,
            action="DRIVER_CREATED",
            ip_address=ip_address,
        )

    def record_driver_updated(
        self,
        *,
        company_id: uuid.UUID,
        user_id: uuid.UUID,
        entity_id: str,
        ip_address: str | None,
    ) -> None:
        """Record driver update."""
        self._repository.create(
            company_id=company_id,
            user_id=user_id,
            entity="driver",
            entity_id=entity_id,
            action="DRIVER_UPDATED",
            ip_address=ip_address,
        )

    def record_driver_deleted(
        self,
        *,
        company_id: uuid.UUID,
        user_id: uuid.UUID,
        entity_id: str,
        ip_address: str | None,
    ) -> None:
        """Record driver soft delete."""
        self._repository.create(
            company_id=company_id,
            user_id=user_id,
            entity="driver",
            entity_id=entity_id,
            action="DRIVER_DELETED",
            ip_address=ip_address,
        )

    def record_truck_created(
        self,
        *,
        company_id: uuid.UUID,
        user_id: uuid.UUID,
        entity_id: str,
        ip_address: str | None,
    ) -> None:
        """Record truck creation."""
        self._repository.create(
            company_id=company_id,
            user_id=user_id,
            entity="truck",
            entity_id=entity_id,
            action="TRUCK_CREATED",
            ip_address=ip_address,
        )

    def record_truck_updated(
        self,
        *,
        company_id: uuid.UUID,
        user_id: uuid.UUID,
        entity_id: str,
        ip_address: str | None,
    ) -> None:
        """Record truck update."""
        self._repository.create(
            company_id=company_id,
            user_id=user_id,
            entity="truck",
            entity_id=entity_id,
            action="TRUCK_UPDATED",
            ip_address=ip_address,
        )

    def record_truck_deleted(
        self,
        *,
        company_id: uuid.UUID,
        user_id: uuid.UUID,
        entity_id: str,
        ip_address: str | None,
    ) -> None:
        """Record truck soft delete."""
        self._repository.create(
            company_id=company_id,
            user_id=user_id,
            entity="truck",
            entity_id=entity_id,
            action="TRUCK_DELETED",
            ip_address=ip_address,
        )

    def record_trailer_created(
        self,
        *,
        company_id: uuid.UUID,
        user_id: uuid.UUID,
        entity_id: str,
        ip_address: str | None,
    ) -> None:
        """Record trailer creation."""
        self._repository.create(
            company_id=company_id,
            user_id=user_id,
            entity="trailer",
            entity_id=entity_id,
            action="TRAILER_CREATED",
            ip_address=ip_address,
        )

    def record_trailer_updated(
        self,
        *,
        company_id: uuid.UUID,
        user_id: uuid.UUID,
        entity_id: str,
        ip_address: str | None,
    ) -> None:
        """Record trailer update."""
        self._repository.create(
            company_id=company_id,
            user_id=user_id,
            entity="trailer",
            entity_id=entity_id,
            action="TRAILER_UPDATED",
            ip_address=ip_address,
        )

    def record_trailer_deleted(
        self,
        *,
        company_id: uuid.UUID,
        user_id: uuid.UUID,
        entity_id: str,
        ip_address: str | None,
    ) -> None:
        """Record trailer soft delete."""
        self._repository.create(
            company_id=company_id,
            user_id=user_id,
            entity="trailer",
            entity_id=entity_id,
            action="TRAILER_DELETED",
            ip_address=ip_address,
        )

    def record_assignment_created(
        self,
        *,
        company_id: uuid.UUID,
        user_id: uuid.UUID,
        entity_id: str,
        ip_address: str | None,
    ) -> None:
        """Record fleet assignment creation."""
        self._repository.create(
            company_id=company_id,
            user_id=user_id,
            entity="fleet_assignment",
            entity_id=entity_id,
            action="ASSIGNMENT_CREATED",
            ip_address=ip_address,
        )

    def record_assignment_removed(
        self,
        *,
        company_id: uuid.UUID,
        user_id: uuid.UUID,
        entity_id: str,
        ip_address: str | None,
    ) -> None:
        """Record fleet assignment removal."""
        self._repository.create(
            company_id=company_id,
            user_id=user_id,
            entity="fleet_assignment",
            entity_id=entity_id,
            action="ASSIGNMENT_REMOVED",
            ip_address=ip_address,
        )

    def record_vehicle_vin_updated(
        self,
        *,
        company_id: uuid.UUID,
        user_id: uuid.UUID,
        entity_id: str,
        old_value: str | None,
        new_value: str,
        ip_address: str | None,
    ) -> None:
        """Record a manual VIN update."""
        self._repository.create(
            company_id=company_id,
            user_id=user_id,
            entity="order_vehicle",
            entity_id=entity_id,
            action="VIN_UPDATED",
            old_value=old_value,
            new_value=new_value,
            ip_address=ip_address,
        )
