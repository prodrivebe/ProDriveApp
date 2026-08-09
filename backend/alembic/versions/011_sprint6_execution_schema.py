"""Sprint 6 vehicle execution and evidence schema."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "011_sprint6_execution_schema"
down_revision: Union[str, None] = "010_stop_progress_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("order_vehicles", sa.Column("original_vin", sa.String(length=17), nullable=True))
    op.add_column("order_vehicles", sa.Column("verified_vin", sa.String(length=17), nullable=True))
    op.add_column(
        "order_vehicles",
        sa.Column("vin_verified_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column("order_vehicles", sa.Column("vin_verified_by", sa.Uuid(), nullable=True))

    op.add_column("vehicle_photos", sa.Column("order_id", sa.Uuid(), nullable=True))
    op.add_column("vehicle_photos", sa.Column("file_name", sa.String(length=255), nullable=True))
    op.add_column("vehicle_photos", sa.Column("file_size", sa.Integer(), nullable=True))
    op.add_column("vehicle_photos", sa.Column("content_type", sa.String(length=100), nullable=True))
    op.add_column("vehicle_photos", sa.Column("metadata", sa.Text(), nullable=True))
    op.create_index("ix_vehicle_photos_order_id", "vehicle_photos", ["order_id"])
    op.create_foreign_key(
        "fk_vehicle_photos_order_id",
        "vehicle_photos",
        "orders",
        ["order_id"],
        ["id"],
    )

    op.create_table(
        "vin_verification_history",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("order_id", sa.Uuid(), nullable=False),
        sa.Column("vehicle_id", sa.Uuid(), nullable=False),
        sa.Column("original_vin", sa.String(length=17), nullable=True),
        sa.Column("verified_vin", sa.String(length=17), nullable=False),
        sa.Column("action", sa.String(length=32), nullable=False),
        sa.Column("verified_by", sa.Uuid(), nullable=True),
        sa.Column(
            "verified_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
        sa.ForeignKeyConstraint(["vehicle_id"], ["order_vehicles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_vin_verification_history_vehicle_id",
        "vin_verification_history",
        ["vehicle_id"],
    )

    op.create_table(
        "vehicle_damage",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("order_id", sa.Uuid(), nullable=False),
        sa.Column("vehicle_id", sa.Uuid(), nullable=False),
        sa.Column("damage_type", sa.String(length=32), nullable=False),
        sa.Column("severity", sa.String(length=32), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("reported_by", sa.Uuid(), nullable=True),
        sa.Column(
            "reported_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
        sa.ForeignKeyConstraint(["vehicle_id"], ["order_vehicles.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_vehicle_damage_order_id", "vehicle_damage", ["order_id"])
    op.create_index("ix_vehicle_damage_vehicle_id", "vehicle_damage", ["vehicle_id"])

    op.create_table(
        "vehicle_damage_photos",
        sa.Column("damage_id", sa.Uuid(), nullable=False),
        sa.Column("photo_id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["damage_id"], ["vehicle_damage.id"]),
        sa.ForeignKeyConstraint(["photo_id"], ["vehicle_photos.id"]),
        sa.PrimaryKeyConstraint("damage_id", "photo_id"),
    )

    op.create_table(
        "order_documents",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("order_id", sa.Uuid(), nullable=False),
        sa.Column("document_type", sa.String(length=32), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("uploaded_by", sa.Uuid(), nullable=True),
        sa.Column(
            "uploaded_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_order_documents_order_id", "order_documents", ["order_id"])
    op.create_index("ix_order_documents_document_type", "order_documents", ["document_type"])

    op.create_table(
        "order_completion_checklist",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("order_id", sa.Uuid(), nullable=False),
        sa.Column("pickup_completed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("delivery_completed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("vins_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("photos_uploaded", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("documents_uploaded", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "damage_reports_completed",
            sa.Boolean(),
            nullable=False,
            server_default="true",
        ),
        sa.Column("can_complete", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("completion_percentage", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"]),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("order_id", name="uq_order_completion_checklist_order_id"),
    )


def downgrade() -> None:
    op.drop_table("order_completion_checklist")
    op.drop_index("ix_order_documents_document_type", table_name="order_documents")
    op.drop_index("ix_order_documents_order_id", table_name="order_documents")
    op.drop_table("order_documents")
    op.drop_table("vehicle_damage_photos")
    op.drop_index("ix_vehicle_damage_vehicle_id", table_name="vehicle_damage")
    op.drop_index("ix_vehicle_damage_order_id", table_name="vehicle_damage")
    op.drop_table("vehicle_damage")
    op.drop_index("ix_vin_verification_history_vehicle_id", table_name="vin_verification_history")
    op.drop_table("vin_verification_history")
    op.drop_constraint("fk_vehicle_photos_order_id", "vehicle_photos", type_="foreignkey")
    op.drop_index("ix_vehicle_photos_order_id", table_name="vehicle_photos")
    op.drop_column("vehicle_photos", "metadata")
    op.drop_column("vehicle_photos", "content_type")
    op.drop_column("vehicle_photos", "file_size")
    op.drop_column("vehicle_photos", "file_name")
    op.drop_column("vehicle_photos", "order_id")
    op.drop_column("order_vehicles", "vin_verified_by")
    op.drop_column("order_vehicles", "vin_verified_at")
    op.drop_column("order_vehicles", "verified_vin")
    op.drop_column("order_vehicles", "original_vin")
