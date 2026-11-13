#!/bin/bash
cd /app && python3 - <<'PY'
from pathlib import Path
p = Path("app/models/order.py"); s = p.read_text()
s = s.replace("    created_at: Mapped[datetime]\n", "    created_at: Mapped[datetime]\n    currency: Mapped[str] = mapped_column(String(3))\n")
p.write_text(s)
Path("migrations/versions/0002_add_currency_to_orders.py").write_text('''"""add_currency_to_orders

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
    op.add_column("orders", sa.Column("currency", sa.String(3), nullable=True))
    op.execute(sa.text("UPDATE orders SET currency = :currency WHERE currency IS NULL").bindparams(currency="GBP"))
    op.alter_column("orders", "currency", existing_type=sa.String(3), nullable=False)


def downgrade() -> None:
    op.drop_column("orders", "currency")
''')
PY
