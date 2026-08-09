"""Shared enumerations."""

from enum import IntEnum, StrEnum


class UserRole(StrEnum):
    """Application user roles."""

    ADMIN = "ADMIN"
    DISPATCHER = "DISPATCHER"
    DRIVER = "DRIVER"


class TrailerCapacity(IntEnum):
    """Supported trailer vehicle capacities."""

    TWO = 2
    THREE = 3
    FIVE = 5
    EIGHT = 8
    TEN = 10

    @classmethod
    def values(cls) -> set[int]:
        """Return supported capacity values."""
        return {capacity.value for capacity in cls}


class OrderStatus(StrEnum):
    """Transport order lifecycle status."""

    DRAFT = "DRAFT"
    READY = "READY"
    ASSIGNED = "ASSIGNED"
    ACCEPTED = "ACCEPTED"
    ARRIVED_PICKUP = "ARRIVED_PICKUP"
    LOADING = "LOADING"
    LOADED = "LOADED"
    IN_TRANSIT = "IN_TRANSIT"
    ARRIVED_DELIVERY = "ARRIVED_DELIVERY"
    DELIVERING = "DELIVERING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class StopProgressStatus(StrEnum):
    """Operational progress for an order stop."""

    PENDING = "PENDING"
    ARRIVED = "ARRIVED"
    LOADING = "LOADING"
    COMPLETED = "COMPLETED"


class StopType(StrEnum):
    """Pickup or delivery stop."""

    PICKUP = "PICKUP"
    DELIVERY = "DELIVERY"


class PhotoType(StrEnum):
    """Vehicle photo categories."""

    FRONT = "FRONT"
    REAR = "REAR"
    LEFT = "LEFT"
    RIGHT = "RIGHT"
    INTERIOR = "INTERIOR"
    DAMAGE = "DAMAGE"
    DOCUMENT = "DOCUMENT"
    CUSTOM = "CUSTOM"


class DocumentType(StrEnum):
    """Stored document categories."""

    CMR = "CMR"
    CMR_SIGNED = "CMR_SIGNED"
    INVOICE = "INVOICE"
    DELIVERY_NOTE = "DELIVERY_NOTE"
    PHOTO_ARCHIVE = "PHOTO_ARCHIVE"
