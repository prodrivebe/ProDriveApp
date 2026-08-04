"""Add order tables."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "005_orders_schema"
down_revision: Union[str, None] = "004_customers_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "orders",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("customer_id", sa.Uuid(), nullable=False),
        sa.Column("order_number", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("assigned_driver_id", sa.Uuid(), nullable=True),
        sa.Column("assigned_truck_id", sa.Uuid(), nullable=True),
        sa.Column("assigned_trailer_id", sa.Uuid(), nullable=True),
        sa.Column("planned_pickup_date", sa.Date(), nullable=True),
        sa.Column("planned_delivery_date", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("updated_by", sa.Uuid(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["assigned_driver_id"], ["drivers.id"]),
        sa.ForeignKeyConstraint(["assigned_trailer_id"], ["trailers.id"]),
        sa.ForeignKeyConstraint(["assigned_truck_id"], ["trucks.id"]),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id", "order_number", name="uq_orders_company_order_number"),
    )
    op.create_index("ix_orders_company_id", "orders", ["company_id"])
    op.create_index("ix_orders_customer_id", "orders", ["customer_id"])
    op.create_index("ix_orders_order_number", "orders", ["order_number"])
    op.create_index("ix_orders_status", "orders", ["status"])
    op.create_index("ix_orders_assigned_driver_id", "orders", ["assigned_driver_id"])

    op.create_table(
        "order_stops",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("order_id", sa.Uuid(), nullable=False),
        sa.Column("stop_type", sa.String(length=16), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("company_name", sa.String(length=255), nullable=True),
        sa.Column("contact_name", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("address", sa.String(length=500), nullable=True),
        sa.Column("city", sa.String(length=100), nullable=True),
        sa.Column("postal_code", sa.String(length=20), nullable=True),
        sa.Column("country", sa.String(length=100), nullable=True),
        sa.Column("latitude", sa.Numeric(10, 7), nullable=True),
        sa.Column("longitude", sa.Numeric(10, 7), nullable=True),
        sa.Column("arrival_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("departure_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("updated_by", sa.Uuid(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_order_stops_company_id", "order_stops", ["company_id"])
    op.create_index("ix_order_stops_order_id", "order_stops", ["order_id"])

    op.create_table(
        "order_vehicles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("order_id", sa.Uuid(), nullable=False),
        sa.Column("pickup_stop_id", sa.Uuid(), nullable=True),
        sa.Column("delivery_stop_id", sa.Uuid(), nullable=True),
        sa.Column("vin", sa.String(length=17), nullable=True),
        sa.Column("make", sa.String(length=100), nullable=True),
        sa.Column("model", sa.String(length=100), nullable=True),
        sa.Column("generation", sa.String(length=100), nullable=True),
        sa.Column("body_type", sa.String(length=100), nullable=True),
        sa.Column("color", sa.String(length=50), nullable=True),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column("fuel_type", sa.String(length=50), nullable=True),
        sa.Column("transmission", sa.String(length=50), nullable=True),
        sa.Column("running", sa.Boolean(), nullable=True),
        sa.Column("estimated_weight", sa.Numeric(10, 2), nullable=True),
        sa.Column("estimated_height", sa.Numeric(10, 2), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("updated_by", sa.Uuid(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["delivery_stop_id"], ["order_stops.id"]),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
        sa.ForeignKeyConstraint(["pickup_stop_id"], ["order_stops.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_order_vehicles_company_id", "order_vehicles", ["company_id"])
    op.create_index("ix_order_vehicles_order_id", "order_vehicles", ["order_id"])
    op.create_index("ix_order_vehicles_vin", "order_vehicles", ["vin"])

    op.create_table(
        "order_timeline",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("order_id", sa.Uuid(), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_order_timeline_company_id", "order_timeline", ["company_id"])
    op.create_index("ix_order_timeline_order_id", "order_timeline", ["order_id"])


def downgrade() -> None:
    op.drop_index("ix_order_timeline_order_id", table_name="order_timeline")
    op.drop_index("ix_order_timeline_company_id", table_name="order_timeline")
    op.drop_table("order_timeline")
    op.drop_index("ix_order_vehicles_vin", table_name="order_vehicles")
    op.drop_index("ix_order_vehicles_order_id", table_name="order_vehicles")
    op.drop_index("ix_order_vehicles_company_id", table_name="order_vehicles")
    op.drop_table("order_vehicles")
    op.drop_index("ix_order_stops_order_id", table_name="order_stops")
    op.drop_index("ix_order_stops_company_id", table_name="order_stops")
    op.drop_table("order_stops")
    op.drop_index("ix_orders_assigned_driver_id", table_name="orders")
    op.drop_index("ix_orders_status", table_name="orders")
    op.drop_index("ix_orders_order_number", table_name="orders")
    op.drop_index("ix_orders_customer_id", table_name="orders")
    op.drop_index("ix_orders_company_id", table_name="orders")
    op.drop_table("orders")
