# shop-api

Order and customer API for the web shop. FastAPI + async SQLAlchemy 2.0 on Postgres, Alembic migrations.

## Layout

Each bounded context lives in `app/<context>/`:

- `routes.py` — FastAPI router; thin handlers, auth dependencies, maps domain errors to HTTP.
- `service.py` — business rules; owns the transaction.
- `repository.py` — all queries for the context's tables.
- `models.py` — SQLAlchemy models.
- `schemas.py` — pydantic request/response bodies.

Outbound integrations (SMS provider, push provider) are thin clients in `app/integrations/`.
Migrations are in `migrations/versions/`, numbered.

## Dev

    uv sync
    uv run alembic upgrade head
    uv run pytest
