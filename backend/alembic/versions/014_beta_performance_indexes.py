"""Sprint 12 performance indexes for common query patterns."""

from typing import Sequence, Union

from alembic import op

revision: str = "014_beta_performance_indexes"
down_revision: Union[str, None] = "013_planning_loading_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_orders_company_status",
        "orders",
        ["company_id", "status"],
        unique=False,
    )
    op.create_index(
        "ix_orders_company_planned_pickup",
        "orders",
        ["company_id", "planned_pickup_date"],
        unique=False,
    )
    op.create_index(
        "ix_notifications_user_read",
        "notifications",
        ["user_id", "read_at"],
        unique=False,
    )
    op.create_index(
        "ix_ai_suggestions_company_status",
        "ai_suggestions",
        ["company_id", "status"],
        unique=False,
    )
    op.create_index(
        "ix_order_timeline_order_created",
        "order_timeline",
        ["order_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_order_timeline_order_created", table_name="order_timeline")
    op.drop_index("ix_ai_suggestions_company_status", table_name="ai_suggestions")
    op.drop_index("ix_notifications_user_read", table_name="notifications")
    op.drop_index("ix_orders_company_planned_pickup", table_name="orders")
    op.drop_index("ix_orders_company_status", table_name="orders")
