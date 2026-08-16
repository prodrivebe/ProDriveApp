"""Shared Belgian demo dataset for QA and development environments."""

from __future__ import annotations

import logging
import uuid
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.ai.models.ai_suggestion import AIAuditLog, AISuggestion
from app.auth.security import hash_password
from app.common.enums import OrderStatus, StopProgressStatus, UserRole
from app.completion_checklist.models import OrderCompletionChecklist
from app.customers.models import Customer, CustomerContact
from app.documents.models import Document
from app.drivers.models import Driver
from app.fleet.models import FleetAssignment
from app.notifications.models import Notification
from app.order_documents.models import OrderDocument
from app.orders.models import Order, OrderStop, OrderTimelineEntry, OrderVehicle
from app.planning.models.loading_plan import LoadingPlan, LoadingPosition
from app.trailers.models import Trailer
from app.trucks.models import Truck
from app.users.models import User
from app.vehicle_damage.models import VehicleDamage, VehicleDamagePhoto
from app.vehicle_photos.models import VehiclePhoto
from app.vin_verification.models import VinVerificationHistory

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Demo account credentials (documented in docs/BETA_TEST_USERS.md)
# ---------------------------------------------------------------------------
DEMO_COMPANY_NAME = "Bruxelles Auto Transport NV"
DEMO_ADMIN_EMAIL = "demo.admin@prodrive.be"
DEMO_ADMIN_PASSWORD = "DemoAdmin123!"
DEMO_DISPATCHER_EMAIL = "demo.dispatcher@prodrive.be"
DEMO_DISPATCHER_PASSWORD = "DemoDispatch123!"
DEMO_DRIVER_PASSWORD = "DemoDriver123!"
DEMO_MOBILE_DRIVER_EMAIL = "driver1@prodrive.demo"
DEMO_MOBILE_DRIVER_PASSWORD = "ProDrive2026!"

DEMO_CUSTOMER_COUNT = 20
DEMO_DRIVER_COUNT = 15
DEMO_TRUCK_COUNT = 10
DEMO_TRAILER_COUNT = 8

_BELGIAN_CITIES = [
    ("Brussels", "Avenue Louise 523", "+32 2 555"),
    ("Antwerp", "Groenplaats 12", "+32 3 555"),
    ("Ghent", "Korenmarkt 45", "+32 9 555"),
    ("Liège", "Place Saint-Lambert 14", "+32 4 555"),
    ("Charleroi", "Boulevard Joseph II 88", "+32 71 555"),
    ("Bruges", "Markt 7", "+32 50 555"),
    ("Namur", "Rue de Fer 22", "+32 81 555"),
    ("Leuven", "Bondgenotenlaan 90", "+32 16 555"),
    ("Mechelen", "Grote Markt 3", "+32 15 555"),
    ("Mons", "Grand Place 5", "+32 65 555"),
    ("Hasselt", "Grote Markt 18", "+32 11 555"),
    ("Kortrijk", "Grote Markt 31", "+32 56 555"),
    ("Ostend", "Kapellestraat 40", "+32 59 555"),
    ("Genk", "Stadsplein 2", "+32 89 555"),
    ("Seraing", "Rue de la Boverie 100", "+32 4 556"),
    ("Turnhout", "Grote Markt 28", "+32 14 555"),
    ("Roeselare", "Grote Markt 9", "+32 51 555"),
    ("Aalst", "Grote Markt 34", "+32 53 555"),
    ("Mouscron", "Place Charles Bojus 6", "+32 56 556"),
    ("Verviers", "Place Verte 11", "+32 87 555"),
]

_CUSTOMER_SUFFIXES = [
    "Auto Logistics",
    "Vehicle Transport",
    "Motors Import",
    "Car Center",
    "Fleet Services",
]

_DRIVER_PROFILES: list[tuple[str, str]] = [
    ("Lucas", "Janssens"),
    ("Sophie", "Maes"),
    ("Thomas", "Claes"),
    ("Emma", "Wouters"),
    ("Noah", "Peeters"),
    ("Marie", "Dubois"),
    ("Louis", "Lambert"),
    ("Charlotte", "Dupont"),
    ("Arthur", "Martin"),
    ("Julie", "Simon"),
    ("Victor", "Lemaire"),
    ("Laura", "Renard"),
    ("Maxime", "Bernard"),
    ("Nina", "Dewilde"),
    ("Pieter", "Vandamme"),
]

_TRUCK_SPECS: list[tuple[str, str, str]] = [
    ("1-PRO-001", "Volvo", "FH16"),
    ("1-PRO-002", "Scania", "R500"),
    ("1-PRO-003", "Mercedes-Benz", "Actros"),
    ("1-PRO-004", "DAF", "XF"),
    ("1-PRO-005", "MAN", "TGX"),
    ("1-PRO-006", "Iveco", "S-Way"),
    ("1-PRO-007", "Volvo", "FM"),
    ("1-PRO-008", "Scania", "S-series"),
    ("2-TRA-009", "Mercedes-Benz", "Arocs"),
    ("2-TRA-010", "Renault", "T High"),
]

_TRAILER_SPECS: list[tuple[str, str, str, int, float, float]] = [
    ("1-TRL-101", "car_carrier", "Rolfo", 8, 4.2, 35000),
    ("1-TRL-102", "car_carrier", "Lohr", 6, 4.0, 28000),
    ("1-TRL-103", "car_carrier", "Kässbohrer", 5, 3.8, 22000),
    ("1-TRL-104", "car_carrier", "Rolfo", 7, 4.1, 32000),
    ("1-TRL-105", "car_carrier", "Lohr", 4, 3.6, 18000),
    ("2-TRL-201", "car_carrier", "CMT", 6, 3.9, 26000),
    ("2-TRL-202", "car_carrier", "Kässbohrer", 8, 4.3, 36000),
    ("2-TRL-203", "car_carrier", "Rolfo", 5, 3.7, 21000),
]


def _build_customers() -> list[dict[str, str | None]]:
    customers: list[dict[str, str | None]] = []
    for index in range(DEMO_CUSTOMER_COUNT):
        city, address, phone_prefix = _BELGIAN_CITIES[index]
        suffix = _CUSTOMER_SUFFIXES[index % len(_CUSTOMER_SUFFIXES)]
        slug = city.lower().replace(" ", "").replace("'", "")
        customers.append(
            {
                "company_name": f"{city} {suffix}",
                "city": city,
                "country": "BE",
                "address": address,
                "email": f"logistics.{index + 1:02d}@{slug}.be",
                "phone": f"{phone_prefix} {index + 1:02d} {index + 1:02d}",
            }
        )
    return customers


def _build_driver_users() -> list[dict[str, str]]:
    drivers: list[dict[str, str]] = []
    for index, (first_name, last_name) in enumerate(_DRIVER_PROFILES[:DEMO_DRIVER_COUNT], start=1):
        drivers.append(
            {
                "first_name": first_name,
                "last_name": last_name,
                "email": f"driver{index:02d}@prodrive.be",
                "phone": f"+3247{index:02d}{index:02d}{index:02d}{index:02d}",
            }
        )
    return drivers


def _build_trucks() -> list[dict[str, str | bool]]:
    return [
        {
            "registration_number": registration,
            "brand": brand,
            "model": model,
            "active": True,
        }
        for registration, brand, model in _TRUCK_SPECS[:DEMO_TRUCK_COUNT]
    ]


def _build_trailers() -> list[dict[str, str | int | float | bool]]:
    return [
        {
            "registration_number": registration,
            "trailer_type": trailer_type,
            "manufacturer": manufacturer,
            "maximum_vehicle_count": capacity,
            "maximum_height": height,
            "maximum_weight": weight,
            "active": True,
        }
        for registration, trailer_type, manufacturer, capacity, height, weight in _TRAILER_SPECS[
            :DEMO_TRAILER_COUNT
        ]
    ]


DEMO_CUSTOMERS = _build_customers()
DEMO_DRIVER_USERS = _build_driver_users()
DEMO_TRUCKS = _build_trucks()
DEMO_TRAILERS = _build_trailers()


def reset_demo_company_data(db: Session, company_id: uuid.UUID) -> None:
    """Remove operational and lookup data so demo seed can recreate a clean QA dataset."""
    loading_plan_ids = select(LoadingPlan.id).where(LoadingPlan.company_id == company_id)
    damage_ids = select(VehicleDamage.id).where(VehicleDamage.company_id == company_id)

    db.execute(delete(VehicleDamagePhoto).where(VehicleDamagePhoto.damage_id.in_(damage_ids)))
    db.execute(delete(VehicleDamage).where(VehicleDamage.company_id == company_id))
    db.execute(delete(VehiclePhoto).where(VehiclePhoto.company_id == company_id))
    db.execute(delete(VinVerificationHistory).where(VinVerificationHistory.company_id == company_id))
    db.execute(delete(LoadingPosition).where(LoadingPosition.loading_plan_id.in_(loading_plan_ids)))
    db.execute(delete(LoadingPlan).where(LoadingPlan.company_id == company_id))
    db.execute(delete(OrderDocument).where(OrderDocument.company_id == company_id))
    db.execute(delete(Document).where(Document.company_id == company_id))
    db.execute(delete(OrderCompletionChecklist).where(OrderCompletionChecklist.company_id == company_id))
    db.execute(delete(Notification).where(Notification.company_id == company_id))
    db.execute(delete(AIAuditLog).where(AIAuditLog.company_id == company_id))
    db.execute(delete(AISuggestion).where(AISuggestion.company_id == company_id))
    db.execute(delete(OrderTimelineEntry).where(OrderTimelineEntry.company_id == company_id))
    db.execute(delete(OrderVehicle).where(OrderVehicle.company_id == company_id))
    db.execute(delete(OrderStop).where(OrderStop.company_id == company_id))
    db.execute(delete(Order).where(Order.company_id == company_id))
    db.execute(delete(FleetAssignment).where(FleetAssignment.company_id == company_id))
    db.execute(delete(CustomerContact).where(CustomerContact.company_id == company_id))
    db.execute(delete(Driver).where(Driver.company_id == company_id))
    db.execute(delete(Truck).where(Truck.company_id == company_id))
    db.execute(delete(Trailer).where(Trailer.company_id == company_id))
    db.execute(delete(Customer).where(Customer.company_id == company_id))
    db.commit()
    logger.info("Demo company data reset for company %s", company_id)


def ensure_demo_users(db: Session, company_id: uuid.UUID) -> None:
    """Ensure demo admin, dispatcher, and driver user accounts exist with known passwords."""
    demo_users = [
        {
            "first_name": "Demo",
            "last_name": "Admin",
            "email": DEMO_ADMIN_EMAIL,
            "password": DEMO_ADMIN_PASSWORD,
            "role": UserRole.ADMIN,
        },
        {
            "first_name": "Demo",
            "last_name": "Dispatcher",
            "email": DEMO_DISPATCHER_EMAIL,
            "password": DEMO_DISPATCHER_PASSWORD,
            "role": UserRole.DISPATCHER,
        },
    ]
    for spec in demo_users:
        user = db.scalar(
            select(User).where(
                User.company_id == company_id,
                User.email == spec["email"].lower(),
            )
        )
        if user is None:
            db.add(
                User(
                    company_id=company_id,
                    first_name=spec["first_name"],
                    last_name=spec["last_name"],
                    email=spec["email"].lower(),
                    password_hash=hash_password(spec["password"]),
                    role=spec["role"],
                    is_active=True,
                )
            )
        else:
            user.first_name = spec["first_name"]
            user.last_name = spec["last_name"]
            user.password_hash = hash_password(spec["password"])
            user.role = spec["role"]
            user.is_active = True

    for spec in DEMO_DRIVER_USERS:
        user = db.scalar(
            select(User).where(
                User.company_id == company_id,
                User.email == spec["email"].lower(),
            )
        )
        if user is None:
            db.add(
                User(
                    company_id=company_id,
                    first_name=spec["first_name"],
                    last_name=spec["last_name"],
                    email=spec["email"].lower(),
                    password_hash=hash_password(DEMO_DRIVER_PASSWORD),
                    role=UserRole.DRIVER,
                    is_active=True,
                )
            )
        else:
            user.first_name = spec["first_name"]
            user.last_name = spec["last_name"]
            user.password_hash = hash_password(DEMO_DRIVER_PASSWORD)
            user.role = UserRole.DRIVER
            user.is_active = True
    db.commit()


def seed_demo_lookup_data(db: Session, company_id: uuid.UUID) -> None:
    """Insert the canonical demo customers, drivers, trucks, and trailers."""
    ensure_demo_users(db, company_id)

    for spec in DEMO_CUSTOMERS:
        db.add(Customer(company_id=company_id, **spec))

    for spec in DEMO_DRIVER_USERS:
        user = db.scalar(
            select(User).where(
                User.company_id == company_id,
                User.email == spec["email"].lower(),
            )
        )
        if user is None:
            continue
        db.add(
            Driver(
                company_id=company_id,
                user_id=user.id,
                phone=spec["phone"],
                active=True,
            )
        )

    for spec in DEMO_TRUCKS:
        db.add(Truck(company_id=company_id, **spec))

    for spec in DEMO_TRAILERS:
        db.add(Trailer(company_id=company_id, **spec))

    db.commit()
    logger.info(
        "Demo lookup data seeded for company %s (%d customers, %d drivers, %d trucks, %d trailers)",
        company_id,
        DEMO_CUSTOMER_COUNT,
        DEMO_DRIVER_COUNT,
        DEMO_TRUCK_COUNT,
        DEMO_TRAILER_COUNT,
    )


def seed_demo_orders(db: Session, company_id: uuid.UUID) -> None:
    """Create realistic demo transport orders across workflow statuses."""
    customers = db.scalars(
        select(Customer).where(Customer.company_id == company_id, Customer.deleted_at.is_(None)).limit(8)
    ).all()
    drivers = db.scalars(
        select(Driver).where(Driver.company_id == company_id, Driver.deleted_at.is_(None)).limit(5)
    ).all()
    trucks = db.scalars(
        select(Truck).where(Truck.company_id == company_id, Truck.deleted_at.is_(None)).limit(5)
    ).all()
    trailers = db.scalars(
        select(Trailer).where(Trailer.company_id == company_id, Trailer.deleted_at.is_(None)).limit(5)
    ).all()

    if len(customers) < 3 or not drivers:
        logger.warning("Skipping demo orders — insufficient lookup data.")
        return

    today = date.today()
    now = datetime.now(tz=timezone.utc)
    routes = [
        ("Antwerp", "Brussels"),
        ("Ghent", "Liège"),
        ("Bruges", "Namur"),
        ("Leuven", "Charleroi"),
        ("Mechelen", "Hasselt"),
        ("Kortrijk", "Brussels"),
        ("Ostend", "Antwerp"),
        ("Genk", "Ghent"),
    ]
    vehicle_sets = [
        [("BMW", "320"), ("Audi", "A4")],
        [("Mercedes-Benz", "C220"), ("Volkswagen", "Golf")],
        [("Volvo", "XC60")],
        [("Peugeot", "308"), ("Renault", "Clio"), ("Citroën", "C3")],
        [("Ford", "Focus"), ("Opel", "Astra")],
        [("Toyota", "Yaris")],
        [("Porsche", "Macan"), ("Jaguar", "F-Pace")],
        [("Tesla", "Model 3")],
    ]
    statuses = [
        OrderStatus.READY,
        OrderStatus.READY,
        OrderStatus.ASSIGNED,
        OrderStatus.ASSIGNED,
        OrderStatus.LOADING,
        OrderStatus.IN_TRANSIT,
        OrderStatus.DELIVERING,
        OrderStatus.COMPLETED,
    ]

    for index, status in enumerate(statuses):
        customer = customers[index % len(customers)]
        pickup_city, delivery_city = routes[index]
        vehicles = vehicle_sets[index]
        order_number = f"PD-{today.year}-{index + 1:04d}"
        pickup_date = today + timedelta(days=index)
        delivery_date = pickup_date + timedelta(days=1 + (index % 2))

        order = Order(
            company_id=company_id,
            customer_id=customer.id,
            order_number=order_number,
            status=status.value,
            planned_pickup_date=pickup_date,
            planned_delivery_date=delivery_date,
            notes="Demo transport order — Belgian car carrier route.",
        )
        if status != OrderStatus.READY:
            driver = drivers[index % len(drivers)]
            order.assigned_driver_id = driver.id
            if trucks:
                order.assigned_truck_id = trucks[index % len(trucks)].id
            if trailers:
                order.assigned_trailer_id = trailers[index % len(trailers)].id

        db.add(order)
        db.flush()

        pickup_stop = OrderStop(
            company_id=company_id,
            order_id=order.id,
            stop_type="PICKUP",
            sequence=1,
            city=pickup_city,
            country="BE",
            progress_status=StopProgressStatus.COMPLETED.value
            if status in {OrderStatus.IN_TRANSIT, OrderStatus.DELIVERING, OrderStatus.COMPLETED}
            else StopProgressStatus.PENDING.value,
        )
        delivery_stop = OrderStop(
            company_id=company_id,
            order_id=order.id,
            stop_type="DELIVERY",
            sequence=2,
            city=delivery_city,
            country="BE",
            progress_status=StopProgressStatus.COMPLETED.value
            if status == OrderStatus.COMPLETED
            else StopProgressStatus.PENDING.value,
        )
        db.add_all([pickup_stop, delivery_stop])
        db.flush()

        for vehicle_index, (make, model) in enumerate(vehicles, start=1):
            db.add(
                OrderVehicle(
                    company_id=company_id,
                    order_id=order.id,
                    pickup_stop_id=pickup_stop.id,
                    delivery_stop_id=delivery_stop.id,
                    make=make,
                    model=model,
                    estimated_weight=1500 + (vehicle_index * 120),
                    estimated_height=1.45 + (vehicle_index * 0.05),
                )
            )

        db.add(
            OrderTimelineEntry(
                company_id=company_id,
                order_id=order.id,
                event_type="ORDER_CREATED",
                description=f"Demo order created for {customer.company_name}.",
                created_at=now - timedelta(hours=24 - index),
            )
        )
        if status != OrderStatus.READY:
            db.add(
                OrderTimelineEntry(
                    company_id=company_id,
                    order_id=order.id,
                    event_type="DRIVER_ASSIGNED",
                    description="Driver assigned for demo workflow.",
                    created_at=now - timedelta(hours=20 - index),
                )
            )

    db.commit()
    logger.info("Seeded %d demo orders for company %s", len(statuses), company_id)


def ensure_demo_lookup_data(db: Session, company_id: uuid.UUID, *, reset: bool = True) -> None:
    """Reset (optional) and recreate demo lookup data. Safe to run repeatedly."""
    if reset:
        reset_demo_company_data(db, company_id)
    seed_demo_lookup_data(db, company_id)
    seed_demo_orders(db, company_id)


def count_demo_entities(db: Session, company_id: uuid.UUID) -> dict[str, int]:
    """Return entity counts for QA verification."""
    return {
        "customers": int(
            db.scalar(
                select(func.count())
                .select_from(Customer)
                .where(Customer.company_id == company_id, Customer.deleted_at.is_(None))
            )
            or 0
        ),
        "drivers": int(
            db.scalar(
                select(func.count())
                .select_from(Driver)
                .where(Driver.company_id == company_id, Driver.deleted_at.is_(None))
            )
            or 0
        ),
        "trucks": int(
            db.scalar(
                select(func.count())
                .select_from(Truck)
                .where(Truck.company_id == company_id, Truck.deleted_at.is_(None))
            )
            or 0
        ),
        "trailers": int(
            db.scalar(
                select(func.count())
                .select_from(Trailer)
                .where(Trailer.company_id == company_id, Trailer.deleted_at.is_(None))
            )
            or 0
        ),
        "orders": int(
            db.scalar(
                select(func.count())
                .select_from(Order)
                .where(Order.company_id == company_id, Order.deleted_at.is_(None))
            )
            or 0
        ),
    }
