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

Typical shared mixins:

| Mixin | Adds |
|-------|------|
| `UUIDPKMixIn` | `id: UUID` PK |
| `CreatedAtMixIn` | `created_at: datetime` |
| `UpdatedAtMixIn` | `updated_at: datetime` |
| `SoftDeleteMixIn` | `deleted_at: datetime | None` |
| `BasicAttributes` | `__tablename__`, metadata helpers |

Table names: `snake_case` plural.

## Registration

Import new models in the module Alembic autogenerate scans (e.g. an `all_models/__init__.py` aggregator).
Wire new routers in the central routing module.

## Repositories

Two patterns — advanced-alchemy preferred for new code:

### advanced-alchemy (new code)
```python
from advanced_alchemy.extensions.fastapi import repository
from myapp.orm.mixins import SoftDeleteRepositoryMixIn
from myapp.my_context.models import MyModel

# With soft delete:
class MyModelRepository(SoftDeleteRepositoryMixIn, repository.SQLAlchemyAsyncRepository[MyModel]):
    model_type = MyModel

# Without soft delete:
class MyModelRepository(repository.SQLAlchemyAsyncRepository[MyModel]):
    model_type = MyModel
```

Built-ins: `get_one_or_none(id=...)`, `list(...)`, `add(instance)`, `delete(instance)`.
Custom methods: `self.session` + `select()` 2.0 style.

### Legacy hand-rolled session repository (existing code only — don't use for new code)
```python
from myapp.repository.database import SQLAlchemyAsyncSessionRepository
from myapp.orm.dependencies import SESSION

class MyModelRepository(SQLAlchemyAsyncSessionRepository[MyModel, CreateSchema, UpdateSchema]):
    def __init__(self, session: AsyncSession = SESSION):
        super().__init__(model=MyModel, session=session)
```

## Services

```python
from advanced_alchemy.extensions.fastapi import service
from myapp.orm.mixins import SoftDeleteServiceMixIn
from myapp.my_context.models import MyModel
from myapp.my_context.repository import MyModelRepository

class MyModelService(
    SoftDeleteServiceMixIn[MyModel, MyModelRepository],
    service.SQLAlchemyAsyncRepositoryService[MyModel, MyModelRepository],
):
    repository_type = MyModelRepository
```

Built-ins: `list_and_count(*filters)`, `get(id)`, `create(data)`, `update(data, item_id=id)`, `delete(id)`, `to_schema(data, schema_type=SchemaCls)`.

## Sessions

- Routes: injected by `alchemy.provide_service(ServiceClass)` — never pass manually
- Background tasks: session manager (`DatabaseSessionManager(async_url)` or equivalent) → `async with session_manager.session() as session:`
- `expire_on_commit=False` — global, don't override
- Service owns commit. Routes never commit/rollback. Writes use `auto_commit=True`.
- Never store session on instance vars outside service/repo

## Queries

```python
from sqlalchemy import select
from sqlalchemy.orm import selectinload

stmt = (
    select(MyModel)
    .where(MyModel.deleted_at.is_(None))
    .options(selectinload(MyModel.related))
    .order_by(MyModel.created_at.desc())
)
results = await self.session.scalars(stmt)
```

- `selectinload` default — avoids N+1
- `joinedload` only for single-row lookups
- Pagination via `alchemy.provide_filters({"pagination_type": "limit_offset"})` — don't hand-roll

## Relationships

```python
parent: Mapped[Parent] = relationship("Parent", back_populates="children", lazy="raise")
```

- `lazy="raise"` on all — forces explicit eager load
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
    errors: Mapped[list["ImportJobError"]] = relationship("ImportJobError", lazy="selectin", ...)

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

- Instance method requires relationship loaded — use `lazy="selectin"` or explicit `selectinload`
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

## JSONB

- `from sqlalchemy.dialects.postgresql import JSONB`
- `Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)`
- GIN index in `__table_args__`: `Index("ix_...", "col", postgresql_using="gin")`

## Writes

```python
# Create
entity = await service.create({"name": "foo"}, auto_commit=True)

# Update
entity = await service.update({"name": "bar"}, item_id=entity_id, auto_commit=True)

# Upsert
entity = await service.upsert({"id": id, "name": "foo"}, auto_commit=True)

# Bulk
entities = await service.upsert_many([...], auto_commit=True)
```

## Raw SQL

Migrations only (`op.execute(text(...))`). Always parameterised — no f-strings in SQL.

## Forbidden

- `query()` legacy API
- Lazy-loaded relationships outside session scope
- ORM queries in route handlers
- Raw SQL with string interpolation
- Cross-context model imports in queries
