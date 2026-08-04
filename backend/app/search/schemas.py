"""Global search API schemas."""

import uuid

from pydantic import BaseModel, Field


class SearchResultItem(BaseModel):
    """Single global search result."""

    type: str
    id: uuid.UUID
    title: str
    subtitle: str | None = None


class SearchResponse(BaseModel):
    """Grouped global search results."""

    orders: list[SearchResultItem] = Field(default_factory=list)
    customers: list[SearchResultItem] = Field(default_factory=list)
    drivers: list[SearchResultItem] = Field(default_factory=list)
    vehicles: list[SearchResultItem] = Field(default_factory=list)
