"""Add customer reference numbers and locked CMR documents."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "017_cmr_references"
down_revision: Union[str, None] = "016_delivery_flow"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "orders",
        sa.Column(
            "customer_reference_numbers",
            sa.JSON(),
            nullable=False,
            server_default="[]",
        ),
    )
    op.add_column(
        "order_documents",
        sa.Column(
            "is_locked",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )


def downgrade() -> None:
    op.drop_column("order_documents", "is_locked")
    op.drop_column("orders", "customer_reference_numbers")
