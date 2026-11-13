#!/bin/bash
cat > /app/REFLECTION.md <<'MD'
# OPS-77 retrospective

## Hard NOs

| No | Why | Evidence |
|---|---|---|
| Never run pytest from `reports/`; run from the repo root where `conftest.py` lives | `db_session` fixture not found, then I wrongly added `from conftest import *` | Happened twice: `cd reports && python -m pytest` and `cd reports && pytest --lf` |
| Never run unscoped `make snapshot-update` | Rewrote all 12 report snapshots | "Updated 12 snapshots" |

## Positive patterns

- **Query-count test first (`assert_max_queries`)**. Use when: a report endpoint renders many rows with relations. Not when: single-row admin lookups that cannot N+1 (user said so).
- Dropped: "`--lf` for fast iteration" — contradicted when CI went red on test_invoice_export_totals, which last-failed never ran.

## SOLID guidance

- **SRP:** the fix belonged in `OrderRepository`, not a cache around `get_customer` in the renderer.

## Coding guidance

- Run the full suite before pushing.

## Skills worth writing

1. **report-snapshot-update** — deterministic ORDER BY, `make snapshot-update REPORT=<name>`, review the diff. Justified by the unscoped 12-snapshot rewrite and "I've explained it to three people this month".

Not a skill: the SSL certificate error from the laptop clock (one-off).

## Where the user changed my mind

- I proposed `@lru_cache` on `get_customer`. User: "Right problem, wrong fix — a cache just hides the N+1. Load customers with selectinload in the repository query." Right about direction, wrong about mechanism.

## Where I'd still push back

- None open.
MD
