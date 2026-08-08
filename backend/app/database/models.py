"""Import all models for Alembic autogenerate support."""

from app.audit.models import AuditLog
from app.auth.models import PasswordResetToken, RefreshToken
from app.companies.models import Company, CompanySettings
from app.customers.models import Customer, CustomerContact
from app.documents.models import Document
from app.drivers.models import Driver
from app.fleet.models import FleetAssignment
from app.notifications.models import DeviceToken, Notification
from app.orders.models import Order, OrderStop, OrderTimelineEntry, OrderVehicle
from app.photos.models import VehiclePhoto
from app.trailers.models import Trailer
from app.trucks.models import Truck
from app.users.models import User

__all__ = [
    "AuditLog",
    "Company",
    "CompanySettings",
    "Customer",
    "CustomerContact",
    "DeviceToken",
    "Document",
    "Driver",
    "FleetAssignment",
    "Notification",
    "Order",
    "OrderStop",
    "OrderTimelineEntry",
    "OrderVehicle",
    "PasswordResetToken",
    "RefreshToken",
    "Trailer",
    "Truck",
    "User",
    "VehiclePhoto",
]
