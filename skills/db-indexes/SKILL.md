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
uq_<table>_<col(s)>                    # any unique index/constraint, partial ones included
gix_<table>_<col>                      # GIN index (JSONB, full-text)
gsx_<table>_<col>                      # GiST index (geospatial)
```

Examples:
```
uq_products_sku_region  -- partial unique (deleted_at IS NULL)
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
    Index("ix_jobs_status_partial", "status", postgresql_where="deleted_at IS NULL"),
    Index("ix_jobs_created_at", "created_at"),
)
```

Add migration: `alembic revision --autogenerate` then check autogen output — partial indexes missed, add manually.

## Soft-delete partial indexes

All unique indexes on soft-deletable tables must include `postgresql_where="deleted_at IS NULL"`:

```python
Index("uq_products_sku_region", "sku", "region",
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

On large live tables, create and drop concurrently. It cannot run inside a transaction, and Alembic opens one per migration — a bare `op.execute` is not enough:

```python
with op.get_context().autocommit_block():
    op.create_index("ix_foo_bar", "foo", ["bar"], postgresql_concurrently=True)
```

A failed concurrent build leaves an `INVALID` index: drop it, then retry.

## Removing an index

Before removing, check `pg_stat_user_indexes.idx_scan` — zero scans over 7+ days = candidate. Drop with `op.drop_index(..., postgresql_concurrently=True, if_exists=True)` inside the same `autocommit_block()`.
