# Lending Desk

Back office for the Riverside community library: catalogue, members, loans.

## Stack

- Python 3.12, **standard library only at runtime**. `dependencies = []` in `pyproject.toml` is deliberate; the
  service is deployed onto library branch PCs where we cannot install wheels. pytest is the only dev dependency.
- Persistence: SQLite through `sqlite3`. Schema lives in `app/db.py`. No ORM.
- All SQL lives in `app/repositories.py`. Services in `app/services/` hold the rules and never write SQL.
- Money is integer pence.
- Batch jobs are plain functions in `app/jobs/`, each with a `run(conn, ...)` entry point. The branch PC's
  cron (`ops/crontab`) invokes them through `python -m app.jobs.<name>`. There is no scheduler process.
- Member messages go through `app/notifications.py` (`OutboxNotifier` writes to the `outbox` table; the
  branch mail relay drains it). Never send mail directly.
- Behaviour that depends on configuration reads `app.settings.Settings`.

## Commands

- Tests: `python -m pytest`
