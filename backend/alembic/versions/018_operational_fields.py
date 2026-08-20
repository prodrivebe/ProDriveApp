"""Add operational fields for customers, drivers, trucks and truck records."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "018_operational_fields"
down_revision: Union[str, None] = "017_cmr_references"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("customers", sa.Column("street", sa.String(length=255), nullable=True))
    op.add_column("customers", sa.Column("house_number", sa.String(length=32), nullable=True))
    op.add_column("customers", sa.Column("postal_code", sa.String(length=20), nullable=True))
    op.add_column("customers", sa.Column("invoice_email", sa.String(length=255), nullable=True))
    op.add_column("customers", sa.Column("dispatch_phone", sa.String(length=50), nullable=True))
    op.add_column(
        "customers",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
    )

    op.add_column("drivers", sa.Column("address", sa.String(length=500), nullable=True))
    op.add_column("drivers", sa.Column("country", sa.String(length=100), nullable=True))
    op.add_column("drivers", sa.Column("date_of_birth", sa.Date(), nullable=True))
    op.add_column("drivers", sa.Column("id_document_number", sa.String(length=100), nullable=True))
    op.add_column("drivers", sa.Column("id_expiry", sa.Date(), nullable=True))
    op.add_column("drivers", sa.Column("driving_licence_expiry", sa.Date(), nullable=True))
    op.add_column("drivers", sa.Column("code95_expiry", sa.Date(), nullable=True))
    op.add_column("drivers", sa.Column("tachograph_card_number", sa.String(length=100), nullable=True))
    op.add_column("drivers", sa.Column("tachograph_card_expiry", sa.Date(), nullable=True))
    op.add_column("drivers", sa.Column("visa_residence_expiry", sa.Date(), nullable=True))

    op.add_column("trucks", sa.Column("current_mileage", sa.Integer(), nullable=True))

    op.create_table(
        "truck_maintenance_records",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("truck_id", sa.Uuid(), nullable=False),
        sa.Column("maintenance_date", sa.Date(), nullable=False),
        sa.Column("mileage", sa.Integer(), nullable=True),
        sa.Column("maintenance_type", sa.String(length=100), nullable=False),
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
        sa.ForeignKeyConstraint(["truck_id"], ["trucks.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_truck_maintenance_records_company_id",
        "truck_maintenance_records",
        ["company_id"],
    )
    op.create_index(
        "ix_truck_maintenance_records_truck_id",
        "truck_maintenance_records",
        ["truck_id"],
    )

    op.create_table(
        "truck_inspection_records",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("truck_id", sa.Uuid(), nullable=False),
        sa.Column("inspection_date", sa.Date(), nullable=False),
        sa.Column("mileage", sa.Integer(), nullable=True),
        sa.Column("inspection_type", sa.String(length=100), nullable=False),
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
        sa.ForeignKeyConstraint(["truck_id"], ["trucks.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_truck_inspection_records_company_id",
        "truck_inspection_records",
        ["company_id"],
    )
    op.create_index(
        "ix_truck_inspection_records_truck_id",
        "truck_inspection_records",
        ["truck_id"],
    )

    op.create_table(
        "truck_tire_records",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("truck_id", sa.Uuid(), nullable=False),
        sa.Column("tire_date", sa.Date(), nullable=False),
        sa.Column("mileage", sa.Integer(), nullable=True),
        sa.Column("tire_type", sa.String(length=100), nullable=False),
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
        sa.ForeignKeyConstraint(["truck_id"], ["trucks.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_truck_tire_records_company_id", "truck_tire_records", ["company_id"])
    op.create_index("ix_truck_tire_records_truck_id", "truck_tire_records", ["truck_id"])


def downgrade() -> None:
    op.drop_index("ix_truck_tire_records_truck_id", table_name="truck_tire_records")
    op.drop_index("ix_truck_tire_records_company_id", table_name="truck_tire_records")
    op.drop_table("truck_tire_records")

    op.drop_index("ix_truck_inspection_records_truck_id", table_name="truck_inspection_records")
    op.drop_index("ix_truck_inspection_records_company_id", table_name="truck_inspection_records")
    op.drop_table("truck_inspection_records")

    op.drop_index("ix_truck_maintenance_records_truck_id", table_name="truck_maintenance_records")
    op.drop_index("ix_truck_maintenance_records_company_id", table_name="truck_maintenance_records")
    op.drop_table("truck_maintenance_records")

    op.drop_column("trucks", "current_mileage")

    op.drop_column("drivers", "visa_residence_expiry")
    op.drop_column("drivers", "tachograph_card_expiry")
    op.drop_column("drivers", "tachograph_card_number")
    op.drop_column("drivers", "code95_expiry")
    op.drop_column("drivers", "driving_licence_expiry")
    op.drop_column("drivers", "id_expiry")
    op.drop_column("drivers", "id_document_number")
    op.drop_column("drivers", "date_of_birth")
    op.drop_column("drivers", "country")
    op.drop_column("drivers", "address")

    op.drop_column("customers", "is_active")
    op.drop_column("customers", "dispatch_phone")
    op.drop_column("customers", "invoice_email")
    op.drop_column("customers", "postal_code")
    op.drop_column("customers", "house_number")
    op.drop_column("customers", "street")
