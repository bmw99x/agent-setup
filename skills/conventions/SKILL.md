---
name: conventions
description: Load when placing a new file, naming a schema/model/enum, wiring auth, or unsure which layer owns something.
---

# Project Conventions

## Bounded context structure

Each bounded context owns its layer end-to-end:

```
<context>/
  models.py       # ORM models
  enums.py        # Enums (never in models.py)
  repository.py   # Data access
  service.py      # Business logic
  schemas.py      # Request/response DTOs
  routes.py       # HTTP handlers
  dependencies.py # FastAPI Depends wiring
```

Dep direction: `routes → service → repository → models`. Domain knows nothing about infra.

## File placement rules

- Enums → `enums.py`, never `models.py`
- Shared infra (base classes, session, mixins) → dedicated infra module, not in any context
- New model → register wherever autogenerate discovery happens (e.g. `all_models/__init__.py`)
- New router → register in the central routing file

## Naming

| Thing | Convention |
|---|---|
| Schema (read) | `<Resource>Datum` |
| Schema (write) | `Upsert<Resource>Datum` |
| Schema (bulk write) | `@dataclass` |
| Error audit table | `<resource>_errors` — FK + timestamp as `failed_at` |

Adapt naming conventions to match existing patterns in the project before defaulting to these.

## Auth

Auth dependencies on the router, not on individual handlers. Never hand-roll token/Bearer checks — use the project's auth dependency.

## Service isolation

Service layer must not import transport, queue, or provider modules directly. Inject side-effects via a handler Protocol — keep service testable without real transport.

## Storage patterns

- Derived/computed values: property from related table — not stored column unless perf requires it
- Error history: audit table with FK + timestamp — not flat `last_error`/`failed_at` columns on the parent row

## Import rules

All imports at top of file — no inline or function-local imports.

Exceptions (require a comment):
- Breaking a real circular import
- `TYPE_CHECKING`-only annotation imports

## Environment

Use a `.env` file at repo root. Never hardcode secrets or environment-specific values.
