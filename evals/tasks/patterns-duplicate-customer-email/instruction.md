# Duplicate customer email returns 500

Registering a customer whose email is already taken (`POST /customers`) blows up with a 500 and a stack trace in the logs. Clients should get a 409 Conflict with a short message saying the email is already registered, so the sign-up form can show it.

The API lives in `/app/app` (FastAPI + SQLAlchemy); the `customers` table already has a unique constraint on `email`. Fix it and add a test.
