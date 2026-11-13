---
name: alembic
description: Use when writing, reviewing, or running Alembic migrations in any SQLAlchemy/Postgres project — triggers on "create migration", "add column", "alembic revision", "migrate schema", "add table", "rename column", "add trigger". Covers autogenerate with alembic-utils (DB functions/triggers)/alembic-postgresql-enum, revision naming, downgrade implementation, partial/JSONB index fixes, expand/contract pattern, and safe DDL on large Postgres tables.
---

# alembic.md

## Tool

Alembic + `alembic-utils` (PGFunction, PGTrigger) + `alembic-postgresql-enum`. Config: `alembic.ini` + the project's migrations dir (often `alembic/` or `migrations/`).

## Workflow: model change → merged migration

1. Edit SQLAlchemy model
2. `alembic revision --autogenerate -m "add_<thing>_to_<table>"` — review output carefully
3. Edit generated script: fix gotchas (see below)
4. `alembic upgrade head` locally — verify applies clean
5. `alembic downgrade -1` — verify downgrade works
6. Commit migration file alongside model change in same PR/MR

(Prefix commands with your project's runner, e.g. `uv run`, `poetry run`.)

## Message naming

Slug format: `<verb>_<what>[_to|_on|_from_<table>]` — imperative, snake_case, descriptive.

```
add_deleted_at_to_users
add_ix_orders_customer_id
create_email_jobs_table
drop_legacy_status_column
alter_order_status_enum
```

## Autogen gotchas

| Issue | Fix |
|-------|-----|
| Enum changes not detected | Use `alembic-postgresql-enum` — handles this |
| PGFunction / PGTrigger | Use `alembic-utils` classes, not raw `op.execute` — see below |
| Partial indexes | Autogen misses `postgresql_where` — add manually |
| JSONB indexes | Not detected — add `op.create_index` manually |
| Table order on create | Check FK deps — reorder `op.create_table` if needed |
| SQLAlchemy `Identity` | Autogen sometimes emits spurious diffs — verify before commit |

## DB functions and triggers (alembic-utils)

Declare each as an entity and register it so autogenerate diffs it:

```python
from alembic_utils.pg_function import PGFunction
from alembic_utils.pg_trigger import PGTrigger

set_updated_at = PGFunction(
    schema="public",
    signature="set_updated_at()",
    definition="RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN NEW.updated_at = now(); RETURN NEW; END $$",
)
orders_set_updated_at = PGTrigger(
    schema="public",
    signature="orders_set_updated_at",
    on_entity="public.orders",
    definition="BEFORE UPDATE ON public.orders FOR EACH ROW EXECUTE FUNCTION public.set_updated_at()",
)
```

- In `env.py`: `from alembic_utils.replaceable_entity import register_entities; register_entities([set_updated_at, orders_set_updated_at])` — unregistered entities are invisible to autogenerate.
- Migration uses `op.create_entity(...)` / `op.replace_entity(...)` / `op.drop_entity(...)`; function before trigger on upgrade, reverse order on downgrade.
- Changing a definition: edit the entity, autogenerate → `replace_entity`, whose downgrade restores the old definition.

## Downgrade

Always implement `downgrade()`. Bare `pass` not acceptable except for data-only migrations with no schema change.

```python
def downgrade() -> None:
    op.drop_index("ix_users_email_domain", table_name="users")
    op.drop_column("users", "deleted_at")
```

## Data migrations

- Backfills in same Alembic script as schema change, using `op.execute(text(...))`
- Parameterised always — no string interpolation
- Idempotent: use `WHERE col IS NULL` or `ON CONFLICT DO NOTHING`
- Large tables: batch by primary-key range (keyset), e.g. loop `UPDATE t SET ... WHERE id > :lo AND id <= :hi AND col IS NULL`. Not `LIMIT/OFFSET`: `UPDATE` has no `LIMIT` and `OFFSET` rescans skipped rows on every batch

## Multi-env

- Same migration applies to all environments
- CI runs `alembic upgrade head` on each merge to the main branch
- Never env-specific migration logic

## Safety

- **Defaults:** on PG11+, `ADD COLUMN ... NOT NULL DEFAULT <constant>` is metadata-only (no rewrite) — do it in one step. A volatile default (`now()`, `gen_random_uuid()`) or PG < 11 rewrites the table: add nullable, backfill, then constrain.
- **Not-null columns needing computed values:** expand/contract: add nullable → backfill → constrain in a later migration. On a large table add `CHECK (col IS NOT NULL) NOT VALID`, then `VALIDATE CONSTRAINT`, then `SET NOT NULL` (PG12+ skips the scan) — avoids a long `ACCESS EXCLUSIVE` scan
- **Rename column:** three-step: add new → copy data → drop old (across deployments if needed)
- **Enum changes:** `alembic-postgresql-enum` handles ADD/REMOVE enum values without full rewrite

## Running

```bash
alembic upgrade head          # apply all pending
alembic downgrade -1          # roll back one
alembic current               # show current revision
alembic history               # show all revisions
alembic show <rev>            # show specific revision
```

## Multiple heads

If autogenerate creates a second head:
```bash
alembic merge heads -m "merge_heads"
```

## Testing migrations

- CI applies migrations on each PR/MR against a clean test DB
- Run locally: `alembic downgrade base && alembic upgrade head`
