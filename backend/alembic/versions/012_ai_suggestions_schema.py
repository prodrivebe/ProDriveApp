"""Sprint 10 AI suggestions and audit schema."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "012_ai_suggestions_schema"
down_revision: Union[str, None] = "011_sprint6_execution_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ai_suggestions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("suggestion_type", sa.String(length=64), nullable=False),
        sa.Column("input_text", sa.Text(), nullable=True),
        sa.Column("output_json", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("prompt_version", sa.String(length=32), nullable=False),
        sa.Column("model_version", sa.String(length=64), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("approved_by", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("related_order_id", sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(["approved_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ai_suggestions_company_id", "ai_suggestions", ["company_id"])
    op.create_index("ix_ai_suggestions_status", "ai_suggestions", ["status"])
    op.create_index("ix_ai_suggestions_suggestion_type", "ai_suggestions", ["suggestion_type"])

    op.create_table(
        "ai_audit_logs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("suggestion_id", sa.Uuid(), nullable=True),
        sa.Column("event_type", sa.String(length=32), nullable=False),
        sa.Column("prompt_version", sa.String(length=32), nullable=False),
        sa.Column("model_version", sa.String(length=64), nullable=False),
        sa.Column("input_text", sa.Text(), nullable=True),
        sa.Column("output_json", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("dispatcher_decision", sa.String(length=32), nullable=True),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["suggestion_id"], ["ai_suggestions.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ai_audit_logs_company_id", "ai_audit_logs", ["company_id"])
    op.create_index("ix_ai_audit_logs_suggestion_id", "ai_audit_logs", ["suggestion_id"])


def downgrade() -> None:
    op.drop_index("ix_ai_audit_logs_suggestion_id", table_name="ai_audit_logs")
    op.drop_index("ix_ai_audit_logs_company_id", table_name="ai_audit_logs")
    op.drop_table("ai_audit_logs")
    op.drop_index("ix_ai_suggestions_suggestion_type", table_name="ai_suggestions")
    op.drop_index("ix_ai_suggestions_status", table_name="ai_suggestions")
    op.drop_index("ix_ai_suggestions_company_id", table_name="ai_suggestions")
    op.drop_table("ai_suggestions")
