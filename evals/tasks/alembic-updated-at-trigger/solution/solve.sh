#!/bin/bash
cat > /app/migrations/versions/0002_add_set_updated_at_trigger_to_orders.py <<'PY'
"""add_set_updated_at_trigger_to_orders

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-12 10:00:00

"""
from alembic import op
from alembic_utils.pg_function import PGFunction
from alembic_utils.pg_trigger import PGTrigger

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

set_updated_at = PGFunction(
    schema="public",
    signature="set_updated_at()",
    definition="""RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$""",
)

orders_set_updated_at = PGTrigger(
    schema="public",
    signature="orders_set_updated_at",
    on_entity="public.orders",
    definition="BEFORE UPDATE ON public.orders FOR EACH ROW EXECUTE FUNCTION public.set_updated_at()",
)


def upgrade() -> None:
    op.create_entity(set_updated_at)
    op.create_entity(orders_set_updated_at)


def downgrade() -> None:
    op.drop_entity(orders_set_updated_at)
    op.drop_entity(set_updated_at)
PY
