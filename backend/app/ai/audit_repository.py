"""AI audit log persistence."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.ai.models.ai_suggestion import AIAuditLog


class AIAuditRepository:
    """Store immutable AI audit records."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def create(
        self,
        *,
        company_id: uuid.UUID,
        user_id: uuid.UUID,
        event_type: str,
        prompt_version: str,
        model_version: str,
        input_text: str | None = None,
        output_json: dict[str, object] | None = None,
        confidence: float | None = None,
        dispatcher_decision: str | None = None,
        suggestion_id: uuid.UUID | None = None,
    ) -> AIAuditLog:
        record = AIAuditLog(
            company_id=company_id,
            suggestion_id=suggestion_id,
            event_type=event_type,
            prompt_version=prompt_version,
            model_version=model_version,
            input_text=input_text,
            output_json=json.dumps(output_json) if output_json is not None else None,
            confidence=confidence,
            dispatcher_decision=dispatcher_decision,
            user_id=user_id,
            created_at=datetime.now(tz=UTC),
        )
        self._db.add(record)
        self._db.commit()
        self._db.refresh(record)
        return record
