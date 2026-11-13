"""create supplier_contact and supplier_import

Revision ID: 0002
Revises: 0001
"""

import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"


def upgrade() -> None:
    op.create_table(
        "supplier_contact",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("supplier_id", sa.Uuid(), sa.ForeignKey("supplier.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(320), nullable=True),
        sa.Column("is_primary", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
    )
    op.create_index("ix_supplier_contact_supplier_id", "supplier_contact", ["supplier_id"])
    op.create_index(
        "uq_supplier_contact_supplier_id_email",
        "supplier_contact",
        ["supplier_id", "email"],
        unique=True,
        postgresql_where=sa.text("email IS NOT NULL"),
    )

    op.create_table(
        "supplier_import",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("started_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ix_supplier_import_status_running",
        "supplier_import",
        ["started_at"],
        postgresql_where=sa.text("status = 'running'"),
    )


def downgrade() -> None:
    pass
