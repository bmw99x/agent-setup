---
name: advanced-alchemy
description: Use when creating or reviewing SQLAlchemy 2.0 async models, repositories, services, or queries with advanced-alchemy — triggers on "create model", "add ORM model", "write repository", "add service method", "write query". Covers Mapped[] columns, advanced-alchemy BasicAttributes/repository/service, UUID PK and soft-delete mixins, selectinload, lazy="raise", JSONB/GIN, soft-delete repo mixin, and forbidden legacy query()/raw SQL.
---

# advanced-alchemy.md

## Version & style

SQLAlchemy 2.0, async, `Mapped[]` typed columns. `select()` 2.0 style only — no legacy `query()`.

## Models

```python
from advanced_alchemy.base import BasicAttributes
from myapp.orm.base import Base
from myapp.orm.mixins import CreatedAtMixIn, SoftDeleteMixIn, UpdatedAtMixIn, UUIDPKMixIn

class MyModel(Base, BasicAttributes, UUIDPKMixIn, CreatedAtMixIn, SoftDeleteMixIn, UpdatedAtMixIn):
    __tablename__ = "my_models"

    name: Mapped[str] = mapped_column(nullable=False)
    value: Mapped[str | None] = mapped_column(nullable=True)
```

Use the project's shared mixins for these columns — never hand-roll `id`/`created_at`/`updated_at`/`deleted_at`. The `*MixIn` names above are house code (`myapp.orm.mixins`): find the project's equivalents first. If it has none, advanced-alchemy ships `UUIDPrimaryKey` and `AuditColumns` (`created_at`/`updated_at`) in `advanced_alchemy.mixins`; soft delete is always house code.

| Mixin | Adds |
|-------|------|
| `UUIDPKMixIn` | `id: UUID` PK |
| `CreatedAtMixIn` | `created_at: datetime` |
| `UpdatedAtMixIn` | `updated_at: datetime` |
| `SoftDeleteMixIn` | `deleted_at: datetime | None` |
| `BasicAttributes` | `to_dict()` only — declare `__tablename__` yourself (`CommonTableAttributes` is the one that derives it) |

Table names: `snake_case` plural.

## Registration

Import new models in the module Alembic autogenerate scans (e.g. an `all_models/__init__.py` aggregator).
Wire new routers in the central routing module.

## Repositories

New code: `repository.SQLAlchemyAsyncRepository[Model]` (from `advanced_alchemy.extensions.fastapi`) with `model_type = Model`; put `SoftDeleteRepositoryMixIn` first in the bases for soft-deletable models. The legacy hand-rolled `SQLAlchemyAsyncSessionRepository` is for existing code only.

Custom methods (`self.session` + `select()`) bypass the soft-delete mixin's filter — add `.where(Model.deleted_at.is_(None))` yourself.

## Services

`service.SQLAlchemyAsyncRepositoryService[Model, ModelRepository]` with `repository_type = ModelRepository`; soft-deletable models put `SoftDeleteServiceMixIn[Model, ModelRepository]` first in the bases. Convert with `service.to_schema(data, schema_type=SchemaCls)`.

## Sessions

- Routes: injected by `alchemy.provide_service(ServiceClass)` — never pass manually
- Background tasks: session manager (`DatabaseSessionManager(async_url)` or equivalent) → `async with session_manager.session() as session:`
- `expire_on_commit=False` — global, don't override
- Service owns commit. Routes never commit/rollback. Writes use `auto_commit=True`.
- Never store session on instance vars outside service/repo

## Queries

- `selectinload` default — avoids N+1; `joinedload` only for single-row lookups
- Pagination via `alchemy.provide_filters({"pagination_type": "limit_offset"})` — don't hand-roll

## Relationships

```python
parent: Mapped[Parent] = relationship("Parent", back_populates="children", lazy="raise")
```

- `lazy="raise"` on all, no exceptions — forces explicit eager load (`selectinload`) at the query
- `back_populates` not `backref`

## Soft delete

- `SoftDeleteMixIn` adds `deleted_at`
- `SoftDeleteRepositoryMixIn` auto-filters `deleted_at IS NULL`
- No hard delete — `service.delete(id)` sets `deleted_at`
- Queries outside repo: add `.where(Model.deleted_at.is_(None))`

## Hybrid properties

Use for derived/computed values — not stored columns.

```python
from sqlalchemy import func, select
from sqlalchemy.ext.hybrid import hybrid_property

class ImportJob(Base, ...):
    errors: Mapped[list["ImportJobError"]] = relationship("ImportJobError", lazy="raise", ...)

    @hybrid_property
    def attempts(self) -> int:
        """Instance-level: count loaded relationship."""
        return len(self.errors)

    @attempts.expression  # type: ignore[no-redef]
    @classmethod
    def attempts(cls) -> object:
        """SQL expression: subquery for use in filters/queries."""
        return (
            select(func.count(ImportJobError.id))
            .where(ImportJobError.import_job_id == cls.id)
            .correlate(cls)
            .scalar_subquery()
        )
```

- Instance method requires the relationship loaded — `selectinload(ImportJob.errors)` in the query
- Expression method enables `Model.attempts > 0` in `where()` clauses

## Error audit trail pattern

Prefer separate `*_errors` table over flat `last_error`/`failed_at` columns.

```python
class ImportJobError(Base, BasicAttributes, UUIDPKMixIn, CreatedAtMixIn):
    __tablename__ = "import_job_errors"
    import_job_id: Mapped[UUID] = mapped_column(ForeignKey("import_jobs.id", ondelete="CASCADE"), index=True)
    error: Mapped[str] = mapped_column(Text, nullable=False)
    # created_at from CreatedAtMixIn serves as failed_at
```

- `created_at` = timestamp of failure — no separate `failed_at` column needed
- Full audit trail of all errors, not just last
- `attempts` derived as hybrid count of error rows
- Append-only child of a soft-deleted parent: no `SoftDeleteMixIn` needed; `ondelete="CASCADE"` only fires if the parent is ever purged

## JSONB

- `from sqlalchemy.dialects.postgresql import JSONB`
- `Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)`
- GIN index in `__table_args__`: `Index("gix_<table>_<col>", "col", postgresql_using="gin")` — db-indexes owns index naming

## Raw SQL

Migrations only (`op.execute(text(...))`). Always parameterised — no f-strings in SQL.

## Forbidden

- `query()` legacy API
- Lazy-loaded relationships outside session scope
- ORM queries in route handlers
- Raw SQL with string interpolation
- Cross-context model imports in queries
