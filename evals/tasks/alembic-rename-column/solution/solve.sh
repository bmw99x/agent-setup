#!/bin/bash
cd /app && python3 - <<'PY'
from pathlib import Path
p = Path("app/models/order.py"); s = p.read_text()
s = s.replace("    status: Mapped[str] = mapped_column(String(32))\n",
              "    status: Mapped[str | None] = mapped_column(String(32))  # deprecated: dropped once all replicas read state\n"
              "    state: Mapped[str | None] = mapped_column(String(32))\n")
p.write_text(s)
Path("migrations/versions/0002_add_state_to_orders.py").write_text('''"""add_state_to_orders

Expand step of renaming orders.status to state: add state and copy status into it.
A later revision drops status once no deployed code reads it.

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-12 10:00:00

"""
import sqlalchemy as sa
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("orders", sa.Column("state", sa.String(32), nullable=True))
    op.alter_column("orders", "status", existing_type=sa.String(32), nullable=True)
    op.execute(sa.text("UPDATE orders SET state = status WHERE state IS NULL"))


def downgrade() -> None:
    op.execute(sa.text("UPDATE orders SET status = state WHERE status IS NULL"))
    op.alter_column("orders", "status", existing_type=sa.String(32), nullable=False)
    op.drop_column("orders", "state")
''')
PY
