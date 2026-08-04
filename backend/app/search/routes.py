"""Global search API routes."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.common.responses import SuccessResponse, success_response
from app.database.session import get_db
from app.orders.permissions import require_order_manager
from app.search.schemas import SearchResponse
from app.search.service import SearchService
from app.users.models import User

router = APIRouter(prefix="/search", tags=["Search"])


def get_search_service(db: Session = Depends(get_db)) -> SearchService:
    """Provide a search service instance."""
    return SearchService(db)


@router.get("", response_model=SuccessResponse[SearchResponse])
def global_search(
    q: str = Query(min_length=1, max_length=100),
    current_user: User = Depends(require_order_manager),
    search_service: SearchService = Depends(get_search_service),
) -> SuccessResponse[SearchResponse]:
    """Search orders, customers, drivers, VINs, and registrations."""
    results = search_service.search(current_user, q)
    return success_response(results)
