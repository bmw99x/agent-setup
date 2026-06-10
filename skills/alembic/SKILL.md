---
name: alembic
description: Use when writing, reviewing, or running Alembic migrations in any SQLAlchemy/Postgres project — triggers on "create migration", "add column", "alembic revision", "migrate schema", "add table", "rename column". Covers autogenerate with alembic-utils/alembic-postgresql-enum, naming verb_noun_to_table, downgrade implementation, partial/JSONB index fixes, expand/contract pattern, and safe DDL on large Postgres tables.
---

# alembic.md

## Tool

Alembic + `alembic-utils` (PGFunction, PGTrigger) + `alembic-postgresql-enum`. Config: `alembic/` at repo root.

## Workflow: model change → merged migration

1. Edit SQLAlchemy model
2. `alembic revision --autogenerate -m "add_<thing>_to_<table>"` — review output carefully
3. Edit generated script: fix gotchas (see below)
4. `alembic upgrade head` locally — verify applies clean
5. `alembic downgrade -1` — verify downgrade works
6. Commit migration file alongside model change in same PR/MR

(Prefix commands with your project's runner, e.g. `uv run`, `poetry run`.)

## Message naming

Slug format: `verb_noun_to_table` — imperative, snake_case, descriptive.

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
| PGFunction / PGTrigger | Use `alembic-utils` classes, not raw `op.execute` |
| Partial indexes | Autogen misses `postgresql_where` — add manually |
| JSONB indexes | Not detected — add `op.create_index` manually |
| Table order on create | Check FK deps — reorder `op.create_table` if needed |
| SQLAlchemy `Identity` | Autogen sometimes emits spurious diffs — verify before commit |

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
- Large tables: chunk via `LIMIT/OFFSET` or use `op.execute` with batch UPDATE

## Multi-env

- Same migration applies to all environments
- CI runs `alembic upgrade head` on each merge to the main branch
- Never env-specific migration logic

## Safety

- **Locking:** `ADD COLUMN` with default = full table rewrite pre-PG11. Use `ADD COLUMN ... DEFAULT NULL` then backfill.
- **Not-null columns:** expand/contract: add nullable → backfill → add constraint separately
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
