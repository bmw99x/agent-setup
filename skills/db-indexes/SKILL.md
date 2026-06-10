---
name: db-indexes
description: Use when adding, removing, or reviewing PostgreSQL indexes — triggers on "add index", "create index", "index this column", "unique constraint", "speed up query". Covers naming (ix_/uq_/gix_/gsx_), partial unique indexes with deleted_at IS NULL for soft delete, JSONB GIN, PostGIS GiST, composite column order, and CREATE INDEX CONCURRENTLY safety in Alembic migrations.
---

# db-indexes.md

## Purpose

Reference for index decisions, naming, and safety rules. Prevents duplicate/conflicting indexes and documents intent.

## Naming convention

```
ix_<table>_<col(s)>                    # standard B-tree
ix_<table>_<col>_partial               # partial index
uq_<table>_<col(s)>                    # unique constraint as index
gix_<table>_<col>                      # GIN index (JSONB, full-text)
gsx_<table>_<col>                      # GiST index (geospatial)
```

Examples:
```
ix_settings_key_domain  -- partial unique (deleted_at IS NULL)
ix_orders_customer_id   -- FK lookup
```

## Adding an index

Before adding, answer:
1. Is this query in a hot path? (check logs / query planner)
2. Does `EXPLAIN ANALYZE` show sequential scan on large table?
3. Is table read-heavy enough to justify write overhead?
4. Does similar index already exist?

Always add in `__table_args__`:

```python
__table_args__ = (
    Index("ix_jobs_status", "status", postgresql_where="deleted_at IS NULL"),
    Index("ix_jobs_created_at", "created_at"),
)
```

Add migration: `alembic revision --autogenerate` then check autogen output — partial indexes missed, add manually.

## Soft-delete partial indexes

All unique indexes on soft-deletable tables must include `postgresql_where="deleted_at IS NULL"`:

```python
Index("ix_settings_key_domain", "key", "domain",
      postgresql_where="deleted_at IS NULL", unique=True)
```

Plain unique index without this condition blocks re-creation after soft delete.

## Composite index column order

Most selective column first. For `(status, created_at)` — if status has 3 values and created_at is high-cardinality, put `created_at` first unless queries always filter on `status`.

## JSONB indexes

Autogen will not create these. Add manually:

```python
Index("gix_documents_metadata", "metadata", postgresql_using="gin")
```

## GiST (geospatial)

For PostGIS geometry columns:

```python
Index("gsx_locations_geom", "geom", postgresql_using="gist")
```

## CREATE INDEX CONCURRENTLY

For existing production tables, use concurrent creation to avoid lock:

```python
# In migration — must be outside transaction
op.execute("CREATE INDEX CONCURRENTLY ix_foo_bar ON foo (bar)")
```

Alembic wraps in transaction by default — add `with op.get_context().autocommit_block():` or use raw `op.execute`.

## Removing an index

Before removing:
1. Check `pg_stat_user_indexes.idx_scan` — zero scans over 7+ days = candidate
2. `DROP INDEX CONCURRENTLY` to avoid lock

```python
op.execute("DROP INDEX CONCURRENTLY IF EXISTS ix_foo_bar")
```

## Current index inventory

> Update this table when indexes added/removed via migration.

| Table | Index | Columns | Type | Notes |
|-------|-------|---------|------|-------|
| settings | `ix_settings_key_domain` | key, domain | B-tree partial unique | `deleted_at IS NULL` |
| orders | `ix_orders_customer_id` | customer_id | B-tree | FK lookup |

_Add new rows here when creating indexes._
