---
name: rota-testing
description: Use when running or writing tests in the rota repo — fixtures, the monday fixture, how to run the suite locally.
---

# rota testing

- Run the suite from the repo root: `APP_ENV=local python -m pytest -q`.
  Any other `APP_ENV` (including unset, which means `dev`) reports to Sentry and pages on-call.
- Use the `monday` fixture from `tests/conftest.py` for dates; build `Shift`s directly, no factories.
