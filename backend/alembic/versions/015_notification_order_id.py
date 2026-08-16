"""Add optional order_id to notifications."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "015_notification_order_id"
down_revision: Union[str, None] = "014_beta_performance_indexes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("notifications", sa.Column("order_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_notifications_order_id_orders",
        "notifications",
        "orders",
        ["order_id"],
        ["id"],
    )
    op.create_index("ix_notifications_order_id", "notifications", ["order_id"])


def downgrade() -> None:
    op.drop_index("ix_notifications_order_id", table_name="notifications")
    op.drop_constraint("fk_notifications_order_id_orders", "notifications", type_="foreignkey")
    op.drop_column("notifications", "order_id")
