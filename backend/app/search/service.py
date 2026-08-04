"""Global search business logic."""

from sqlalchemy.orm import Session

from app.search.repository import SearchRepository
from app.search.schemas import SearchResponse, SearchResultItem
from app.users.models import User


class SearchService:
    """Global search across business entities."""

    def __init__(self, db: Session) -> None:
        self._repository = SearchRepository(db)

    def search(self, current_user: User, query: str) -> SearchResponse:
        """Search orders, customers, drivers, and vehicles."""
        normalized_query = query.strip()
        if not normalized_query:
            return SearchResponse()

        company_id = current_user.company_id
        orders = self._repository.search_orders(company_id, normalized_query)
        customers = self._repository.search_customers(company_id, normalized_query)
        drivers = self._repository.search_drivers(company_id, normalized_query)
        vehicles = self._repository.search_vehicles(company_id, normalized_query)
        trucks = self._repository.search_trucks_by_registration(company_id, normalized_query)

        order_items = [
            SearchResultItem(
                type="order",
                id=order.id,
                title=order.order_number,
                subtitle=order.status,
            )
            for order in orders
        ]
        customer_items = [
            SearchResultItem(
                type="customer",
                id=customer.id,
                title=customer.company_name,
                subtitle=customer.city,
            )
            for customer in customers
        ]
        driver_items = [
            SearchResultItem(
                type="driver",
                id=driver.id,
                title=f"{user.first_name} {user.last_name}".strip(),
                subtitle=driver.phone,
            )
            for driver, user in drivers
        ]
        vehicle_items = [
            SearchResultItem(
                type="vehicle",
                id=vehicle.id,
                title=vehicle.vin or f"{vehicle.make or ''} {vehicle.model or ''}".strip(),
                subtitle=str(vehicle.order_id),
            )
            for vehicle in vehicles
        ]
        vehicle_items.extend(
            SearchResultItem(
                type="truck",
                id=truck.id,
                title=truck.registration_number,
                subtitle=f"{truck.brand or ''} {truck.model or ''}".strip() or None,
            )
            for truck in trucks
        )
        return SearchResponse(
            orders=order_items,
            customers=customer_items,
            drivers=driver_items,
            vehicles=vehicle_items,
        )
