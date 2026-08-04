"""Add document and photo tables."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "006_documents_schema"
down_revision: Union[str, None] = "005_orders_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "vehicle_photos",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("vehicle_id", sa.Uuid(), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("photo_type", sa.String(length=32), nullable=False),
        sa.Column("uploaded_by", sa.Uuid(), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("gps_latitude", sa.Numeric(10, 7), nullable=True),
        sa.Column("gps_longitude", sa.Numeric(10, 7), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["vehicle_id"], ["order_vehicles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_vehicle_photos_company_id", "vehicle_photos", ["company_id"])
    op.create_index("ix_vehicle_photos_vehicle_id", "vehicle_photos", ["vehicle_id"])

    op.create_table(
        "documents",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("order_id", sa.Uuid(), nullable=False),
        sa.Column("document_type", sa.String(length=32), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("generated_by", sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_documents_company_id", "documents", ["company_id"])
    op.create_index("ix_documents_order_id", "documents", ["order_id"])
    op.create_index("ix_documents_document_type", "documents", ["document_type"])


def downgrade() -> None:
    op.drop_index("ix_documents_document_type", table_name="documents")
    op.drop_index("ix_documents_order_id", table_name="documents")
    op.drop_index("ix_documents_company_id", table_name="documents")
    op.drop_table("documents")
    op.drop_index("ix_vehicle_photos_vehicle_id", table_name="vehicle_photos")
    op.drop_index("ix_vehicle_photos_company_id", table_name="vehicle_photos")
    op.drop_table("vehicle_photos")
