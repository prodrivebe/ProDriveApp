"""Add company settings table."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002_company_settings"
down_revision: Union[str, None] = "001_initial_auth_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "company_settings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("timezone", sa.String(length=64), nullable=False),
        sa.Column("default_currency", sa.String(length=3), nullable=False),
        sa.Column("order_number_prefix", sa.String(length=20), nullable=True),
        sa.Column("require_vehicle_photos", sa.Boolean(), nullable=False),
        sa.Column("primary_color", sa.String(length=7), nullable=False),
        sa.Column("secondary_color", sa.String(length=7), nullable=False),
        sa.Column("accent_color", sa.String(length=7), nullable=False),
        sa.Column("dashboard_title", sa.String(length=255), nullable=True),
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
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id"),
    )
    op.create_index("ix_company_settings_company_id", "company_settings", ["company_id"])


def downgrade() -> None:
    op.drop_index("ix_company_settings_company_id", table_name="company_settings")
    op.drop_table("company_settings")
