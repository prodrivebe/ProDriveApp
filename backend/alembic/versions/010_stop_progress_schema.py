"""Add stop progress tracking for driver workflow."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "010_stop_progress_schema"
down_revision: Union[str, None] = "009_fleet_assignments_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "order_stops",
        sa.Column(
            "progress_status",
            sa.String(length=16),
            nullable=False,
            server_default="PENDING",
        ),
    )
    op.create_index(
        "ix_order_stops_progress_status",
        "order_stops",
        ["progress_status"],
    )


def downgrade() -> None:
    op.drop_index("ix_order_stops_progress_status", table_name="order_stops")
    op.drop_column("order_stops", "progress_status")
