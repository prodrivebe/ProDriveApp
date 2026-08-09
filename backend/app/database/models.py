"""Import all models for Alembic autogenerate support."""

from app.ai.models.ai_suggestion import AIAuditLog, AISuggestion
from app.audit.models import AuditLog
from app.auth.models import PasswordResetToken, RefreshToken
from app.companies.models import Company, CompanySettings
from app.customers.models import Customer, CustomerContact
from app.completion_checklist.models import OrderCompletionChecklist
from app.documents.models import Document
from app.drivers.models import Driver
from app.fleet.models import FleetAssignment
from app.notifications.models import DeviceToken, Notification
from app.order_documents.models import OrderDocument
from app.orders.models import Order, OrderStop, OrderTimelineEntry, OrderVehicle
from app.photos.models import VehiclePhoto
from app.trailers.models import Trailer
from app.trucks.models import Truck
from app.users.models import User
from app.vehicle_damage.models import VehicleDamage, VehicleDamagePhoto
from app.vin_verification.models import VinVerificationHistory

__all__ = [
    "AIAuditLog",
    "AISuggestion",
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
    "OrderCompletionChecklist",
    "OrderDocument",
    "OrderStop",
    "OrderTimelineEntry",
    "OrderVehicle",
    "PasswordResetToken",
    "RefreshToken",
    "Trailer",
    "Truck",
    "User",
    "VehicleDamage",
    "VehicleDamagePhoto",
    "VehiclePhoto",
    "VinVerificationHistory",
]
