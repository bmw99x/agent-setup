"""create customer_devices

Revision ID: 0003
"""

import sqlalchemy as sa
from alembic import op

revision = "0003"
down_revision = "0002"


def upgrade() -> None:
    op.create_table(
        "customer_devices",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("customer_id", sa.Uuid(), sa.ForeignKey("customers.id"), nullable=False, index=True),
        sa.Column("push_token", sa.String(512), nullable=False),
        sa.Column("platform", sa.String(16), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("customer_devices")
