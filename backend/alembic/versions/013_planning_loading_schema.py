"""Sprint 11 planning and loading schema."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "013_planning_loading_schema"
down_revision: Union[str, None] = "012_ai_suggestions_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "loading_plans",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("order_id", sa.Uuid(), nullable=False),
        sa.Column("trailer_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("route_sequence_json", sa.Text(), nullable=True),
        sa.Column("estimated_total_height", sa.Numeric(8, 2), nullable=True),
        sa.Column("estimated_total_weight", sa.Numeric(10, 2), nullable=True),
        sa.Column("estimated_travel_km", sa.Numeric(10, 2), nullable=True),
        sa.Column("front_axle_percent", sa.Numeric(5, 2), nullable=True),
        sa.Column("rear_axle_percent", sa.Numeric(5, 2), nullable=True),
        sa.Column("validation_warnings_json", sa.Text(), nullable=True),
        sa.Column("ai_generated", sa.Boolean(), nullable=False),
        sa.Column("confirmed_by", sa.Uuid(), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("updated_by", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_loading_plans_company_id", "loading_plans", ["company_id"])
    op.create_index("ix_loading_plans_order_id", "loading_plans", ["order_id"])
    op.create_index("ix_loading_plans_status", "loading_plans", ["status"])

    op.create_table(
        "loading_positions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("loading_plan_id", sa.Uuid(), nullable=False),
        sa.Column("vehicle_id", sa.Uuid(), nullable=False),
        sa.Column("upper_deck", sa.Boolean(), nullable=False),
        sa.Column("trailer_position", sa.Integer(), nullable=False),
        sa.Column("loading_order", sa.Integer(), nullable=False),
        sa.Column("unloading_order", sa.Integer(), nullable=False),
        sa.Column("destination_city", sa.String(length=100), nullable=True),
        sa.Column("confirmed_by_dispatcher", sa.Boolean(), nullable=False),
        sa.Column("ai_generated", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["loading_plan_id"], ["loading_plans.id"]),
        sa.ForeignKeyConstraint(["vehicle_id"], ["order_vehicles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_loading_positions_company_id", "loading_positions", ["company_id"])
    op.create_index("ix_loading_positions_loading_plan_id", "loading_positions", ["loading_plan_id"])


def downgrade() -> None:
    op.drop_index("ix_loading_positions_loading_plan_id", table_name="loading_positions")
    op.drop_index("ix_loading_positions_company_id", table_name="loading_positions")
    op.drop_table("loading_positions")
    op.drop_index("ix_loading_plans_status", table_name="loading_plans")
    op.drop_index("ix_loading_plans_order_id", table_name="loading_plans")
    op.drop_index("ix_loading_plans_company_id", table_name="loading_plans")
    op.drop_table("loading_plans")
