"""Extend stop progress status for delivery confirmation."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "016_delivery_flow"
down_revision: Union[str, None] = "015_notification_order_id"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "order_stops",
        "progress_status",
        existing_type=sa.String(length=16),
        type_=sa.String(length=32),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "order_stops",
        "progress_status",
        existing_type=sa.String(length=32),
        type_=sa.String(length=16),
        existing_nullable=False,
    )
