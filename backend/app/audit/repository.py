"""Audit log persistence layer."""

import uuid

from sqlalchemy.orm import Session

from app.audit.models import AuditLog


class AuditRepository:
    """Repository for audit log records."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def create(
        self,
        *,
        company_id: uuid.UUID,
        user_id: uuid.UUID | None,
        entity: str,
        entity_id: str | None,
        action: str,
        old_value: str | None = None,
        new_value: str | None = None,
        ip_address: str | None = None,
    ) -> AuditLog:
        """Persist an audit log entry."""
        audit_log = AuditLog(
            company_id=company_id,
            user_id=user_id,
            entity=entity,
            entity_id=entity_id,
            action=action,
            old_value=old_value,
            new_value=new_value,
            ip_address=ip_address,
        )
        self._db.add(audit_log)
        self._db.commit()
        self._db.refresh(audit_log)
        return audit_log
