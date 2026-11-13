#!/bin/bash
set -euo pipefail
cd /app
rm app/signups.py
cat > app/registrations.py <<'PY'
from dataclasses import dataclass, field
from itertools import count
from typing import Literal

from app import events

Plan = Literal["free", "pro"]

_next_registration_id = count(1)
_registrations: dict[int, "Registration"] = {}


@dataclass(frozen=True)
class Registration:
    email: str
    plan: Plan
    registration_id: int = field(default_factory=lambda: next(_next_registration_id))


class DuplicateRegistrationError(Exception):
    pass


def create_registration(email: str, plan: Plan) -> Registration:
    normalised_email = email.strip().lower()
    if any(r.email == normalised_email for r in _registrations.values()):
        raise DuplicateRegistrationError(normalised_email)
    registration = Registration(email=normalised_email, plan=plan)
    _registrations[registration.registration_id] = registration
    events.publish("signup.created", {"signupId": registration.registration_id, "plan": registration.plan})
    return registration


def find_registration(registration_id: int) -> Registration | None:
    return _registrations.get(registration_id)


def registration_to_json(registration: Registration) -> dict:
    return {"signupId": registration.registration_id, "email": registration.email, "plan": registration.plan}
PY
cat > app/api.py <<'PY'
"""HTTP handlers. `dispatch` is what the web server calls."""
from app.registrations import (
    DuplicateRegistrationError,
    create_registration,
    find_registration,
    registration_to_json,
)


def post_registration(body: dict) -> tuple[int, dict]:
    try:
        registration = create_registration(body["email"], body["plan"])
    except DuplicateRegistrationError:
        return 409, {"error": "email already signed up"}
    return 201, registration_to_json(registration)


def get_registration(registration_id: int) -> tuple[int, dict]:
    registration = find_registration(registration_id)
    if registration is None:
        return 404, {"error": "not found"}
    return 200, registration_to_json(registration)


def dispatch(method: str, path: str, body: dict | None = None) -> tuple[int, dict]:
    parts = path.strip("/").split("/")
    if method == "POST" and parts == ["signups"]:
        return post_registration(body or {})
    if method == "GET" and len(parts) == 2 and parts[0] == "signups":
        return get_registration(int(parts[1]))
    return 404, {"error": "no route"}
PY
cat > QUESTIONS.md <<'MD'
# Questions

## Rename the public contract too? (`/signups`, `signupId`, `signup.created`)

I renamed everything internal to "registration". I left the wire contract alone because the mobile
app (store-released) and billing-service depend on it: the `/signups` routes, the `signupId` JSON
field and the `signup.created` event.

I'd recommend adding `/registrations` + `registrationId` + `registration.created` alongside the old
names, migrating the app and billing-service, then removing the old names in a later release — a
hard rename would break app versions already installed. The alternative is to keep the old wire
names permanently and treat them as legacy. Go with the additive migration?
MD
python3 -m pytest -q tests
