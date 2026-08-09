"""Completion checklist API schemas."""

from pydantic import BaseModel, Field


class CompletionChecklistResponse(BaseModel):
    """Persisted and computed completion checklist."""

    pickup_completed: bool
    delivery_completed: bool
    vins_verified: bool
    photos_uploaded: bool
    documents_uploaded: bool
    damage_reports_completed: bool
    can_complete: bool
    completion_percentage: int
    completed_items: list[str] = Field(default_factory=list)
    missing_items: list[str] = Field(default_factory=list)


class CompletionValidationResponse(CompletionChecklistResponse):
    """Validation response for order completion."""

    can_complete: bool
