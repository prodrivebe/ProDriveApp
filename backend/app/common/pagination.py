"""Pagination helpers."""

import math
from typing import Any

from pydantic import BaseModel


class PaginationMeta(BaseModel):
    """Pagination metadata."""

    page: int
    page_size: int
    total: int
    pages: int


class PaginatedResponse[T](BaseModel):
    """Paginated success response envelope."""

    success: bool = True
    data: list[T]
    pagination: PaginationMeta


def paginated_response[T](
    *,
    items: list[T],
    page: int,
    page_size: int,
    total: int,
) -> PaginatedResponse[T]:
    """Build a paginated success response."""
    pages = math.ceil(total / page_size) if total > 0 else 0
    return PaginatedResponse(
        data=items,
        pagination=PaginationMeta(
            page=page,
            page_size=page_size,
            total=total,
            pages=pages,
        ),
    )


def build_list_meta(page: int, page_size: int, total: int) -> dict[str, Any]:
    """Build pagination metadata for standard list responses."""
    pages = math.ceil(total / page_size) if total > 0 else 0
    return {
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total": total,
            "pages": pages,
        }
    }
