#!/bin/bash
cd /app && python3 - <<'PY'
from pathlib import Path
p = Path("app/models/order.py"); s = p.read_text()
s = s.replace("from sqlalchemy import Numeric, String", "from sqlalchemy import Index, Numeric, String")
s = s.replace('    __tablename__ = "orders"\n', '    __tablename__ = "orders"\n    __table_args__ = (Index("ix_orders_customer_id", "customer_id"),)\n')
p.write_text(s)
Path("migrations/versions/0002_add_ix_orders_customer_id.py").write_text('''"""add ix_orders_customer_id

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-12 10:00:00

"""
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute("CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_orders_customer_id ON orders (customer_id)")


def downgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute("DROP INDEX CONCURRENTLY IF EXISTS ix_orders_customer_id")
''')
PY
