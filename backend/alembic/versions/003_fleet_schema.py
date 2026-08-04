"""Add fleet tables."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003_fleet_schema"
down_revision: Union[str, None] = "002_company_settings"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "drivers",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("driving_license", sa.String(length=100), nullable=True),
        sa.Column("adr_certificate", sa.String(length=100), nullable=True),
        sa.Column("notes", sa.String(length=1000), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False),
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
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id", "user_id", name="uq_drivers_company_user"),
    )
    op.create_index("ix_drivers_company_id", "drivers", ["company_id"])
    op.create_index("ix_drivers_user_id", "drivers", ["user_id"])

    op.create_table(
        "trucks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("registration_number", sa.String(length=32), nullable=False),
        sa.Column("brand", sa.String(length=100), nullable=True),
        sa.Column("model", sa.String(length=100), nullable=True),
        sa.Column("vin", sa.String(length=32), nullable=True),
        sa.Column("capacity", sa.Integer(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "company_id",
            "registration_number",
            name="uq_trucks_company_registration",
        ),
    )
    op.create_index("ix_trucks_company_id", "trucks", ["company_id"])

    op.create_table(
        "trailers",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("registration_number", sa.String(length=32), nullable=False),
        sa.Column("manufacturer", sa.String(length=100), nullable=True),
        sa.Column("model", sa.String(length=100), nullable=True),
        sa.Column("trailer_type", sa.String(length=100), nullable=True),
        sa.Column("maximum_height", sa.Numeric(8, 2), nullable=True),
        sa.Column("maximum_weight", sa.Numeric(10, 2), nullable=True),
        sa.Column("maximum_vehicle_count", sa.Integer(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "company_id",
            "registration_number",
            name="uq_trailers_company_registration",
        ),
    )
    op.create_index("ix_trailers_company_id", "trailers", ["company_id"])


def downgrade() -> None:
    op.drop_index("ix_trailers_company_id", table_name="trailers")
    op.drop_table("trailers")
    op.drop_index("ix_trucks_company_id", table_name="trucks")
    op.drop_table("trucks")
    op.drop_index("ix_drivers_user_id", table_name="drivers")
    op.drop_index("ix_drivers_company_id", table_name="drivers")
    op.drop_table("drivers")
