# onboarding-service

Takes new customer sign-ups from the mobile app and tells the rest of the platform about them.

- HTTP: `POST /signups`, `GET /signups/{id}` (JSON, camelCase). Called by the mobile app (iOS/Android v3, released through the app stores).
- Events: publishes `signup.created`; consumed by billing-service to open a trial.

Run tests: `python -m pytest`
