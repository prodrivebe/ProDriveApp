"""Add fleet assignments table."""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "009_fleet_assignments_schema"
down_revision: str | None = "008_device_tokens_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "fleet_assignments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("driver_id", sa.Uuid(), nullable=False),
        sa.Column("truck_id", sa.Uuid(), nullable=False),
        sa.Column("trailer_id", sa.Uuid(), nullable=False),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("unassigned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["driver_id"], ["drivers.id"]),
        sa.ForeignKeyConstraint(["truck_id"], ["trucks.id"]),
        sa.ForeignKeyConstraint(["trailer_id"], ["trailers.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_fleet_assignments_company_id",
        "fleet_assignments",
        ["company_id"],
    )
    op.create_index(
        "ix_fleet_assignments_driver_id",
        "fleet_assignments",
        ["driver_id"],
    )
    op.create_index(
        "ix_fleet_assignments_truck_id",
        "fleet_assignments",
        ["truck_id"],
    )
    op.create_index(
        "ix_fleet_assignments_trailer_id",
        "fleet_assignments",
        ["trailer_id"],
    )
    op.create_index(
        "uq_fleet_assignments_active_driver",
        "fleet_assignments",
        ["company_id", "driver_id"],
        unique=True,
        postgresql_where=sa.text("active IS TRUE"),
    )
    op.create_index(
        "uq_fleet_assignments_active_truck",
        "fleet_assignments",
        ["company_id", "truck_id"],
        unique=True,
        postgresql_where=sa.text("active IS TRUE"),
    )
    op.create_index(
        "uq_fleet_assignments_active_trailer",
        "fleet_assignments",
        ["company_id", "trailer_id"],
        unique=True,
        postgresql_where=sa.text("active IS TRUE"),
    )


def downgrade() -> None:
    op.drop_index("uq_fleet_assignments_active_trailer", table_name="fleet_assignments")
    op.drop_index("uq_fleet_assignments_active_truck", table_name="fleet_assignments")
    op.drop_index("uq_fleet_assignments_active_driver", table_name="fleet_assignments")
    op.drop_index("ix_fleet_assignments_trailer_id", table_name="fleet_assignments")
    op.drop_index("ix_fleet_assignments_truck_id", table_name="fleet_assignments")
    op.drop_index("ix_fleet_assignments_driver_id", table_name="fleet_assignments")
    op.drop_index("ix_fleet_assignments_company_id", table_name="fleet_assignments")
    op.drop_table("fleet_assignments")
