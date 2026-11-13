# Service configuration

The service needs a configuration object. Create `/app/app/config/settings.py` exposing a module-level `settings` instance with:

- `database_url` — from `DATABASE_URL`, required
- `sentry_dsn` — from `SENTRY_DSN`, optional (absent means Sentry is disabled)
- `log_level` — from `LOG_LEVEL`, defaults to `INFO`

Values come from environment variables. Developers keep them in a `.env` file at the repository root (`/app/.env`, see `.env.example`); the API, the tests and the worker (`/app/worker`) are each started from a different working directory and must all pick it up.
