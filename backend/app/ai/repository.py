"""AI suggestion persistence."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.ai.models.ai_suggestion import AISuggestion
from app.common.enums import AISuggestionStatus, AISuggestionType


class AISuggestionRepository:
    """Database access for AI suggestions."""

    def __init__(self, db: Session) -> None:
        self._db = db

    def create(
        self,
        *,
        company_id: uuid.UUID,
        suggestion_type: AISuggestionType,
        input_text: str | None,
        output_json: dict[str, object],
        confidence: float,
        prompt_version: str,
        model_version: str,
        created_by: uuid.UUID,
        related_order_id: uuid.UUID | None = None,
    ) -> AISuggestion:
        suggestion = AISuggestion(
            company_id=company_id,
            suggestion_type=suggestion_type.value,
            input_text=input_text,
            output_json=json.dumps(output_json),
            confidence=confidence,
            status=AISuggestionStatus.PENDING.value,
            prompt_version=prompt_version,
            model_version=model_version,
            created_by=created_by,
            created_at=datetime.now(tz=UTC),
            related_order_id=related_order_id,
        )
        self._db.add(suggestion)
        self._db.commit()
        self._db.refresh(suggestion)
        return suggestion

    def get_by_id_for_company(
        self,
        suggestion_id: uuid.UUID,
        company_id: uuid.UUID,
    ) -> AISuggestion | None:
        return (
            self._db.query(AISuggestion)
            .filter(
                AISuggestion.id == suggestion_id,
                AISuggestion.company_id == company_id,
            )
            .one_or_none()
        )

    def list_for_company(
        self,
        company_id: uuid.UUID,
        *,
        status: AISuggestionStatus | None = None,
        suggestion_type: AISuggestionType | None = None,
    ) -> list[AISuggestion]:
        query = self._db.query(AISuggestion).filter(AISuggestion.company_id == company_id)
        if status is not None:
            query = query.filter(AISuggestion.status == status.value)
        if suggestion_type is not None:
            query = query.filter(AISuggestion.suggestion_type == suggestion_type.value)
        return query.order_by(AISuggestion.created_at.desc()).all()

    def update_status(
        self,
        suggestion: AISuggestion,
        *,
        status: AISuggestionStatus,
        approved_by: uuid.UUID | None = None,
        output_json: dict[str, object] | None = None,
        related_order_id: uuid.UUID | None = None,
    ) -> AISuggestion:
        suggestion.status = status.value
        suggestion.approved_by = approved_by
        suggestion.approved_at = datetime.now(tz=UTC) if approved_by else None
        if output_json is not None:
            suggestion.output_json = json.dumps(output_json)
        if related_order_id is not None:
            suggestion.related_order_id = related_order_id
        self._db.add(suggestion)
        self._db.commit()
        self._db.refresh(suggestion)
        return suggestion
