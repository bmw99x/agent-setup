import json
from pathlib import Path

AUTH_88 = """## Why
Credential-stuffing traffic against /signin tripled in September. We need to slow repeated
guessing against a single account.

## What
Lock an account for 30 minutes after 5 consecutive failed sign-ins. While locked, every sign-in
attempt is rejected with `account_locked` and a `Retry-After` header. A successful sign-in resets
the failure count.

## Acceptance criteria
- [ ] After 5 consecutive failed sign-ins the account is locked for 30 minutes
- [ ] Sign-in attempts during the lock are rejected with `account_locked` and `Retry-After`
- [ ] A successful sign-in resets the failure count
- [ ] Support runbook explains how long a customer must wait

## Design
Spec: `docs/specs/login-throttling.md` in the auth-service repo.
Mirrored for the support team on the wiki: `security/login-throttling`
(`wiki show security/login-throttling`).

## Open
- **Blocking:** does support need a manual unlock action? Waiting on support lead.
"""

AUTH_91 = """## Why
Password reset emails take up to 2 minutes to arrive.

## What
Send reset emails from the priority queue.
"""

WIKI_THROTTLING = """Owner: auth team. Source of truth: ticket AUTH-88.

## What customers see
After **5 wrong passwords in a row** the account is **locked for 30 minutes**. The sign-in page
shows "Your account is temporarily locked".

## What to tell the customer
Ask them to wait 30 minutes from their last attempt, then sign in again or reset their password.
There is no manual unlock yet.
"""

WIKI_RESET = """## Password reset
Reset links expire after 1 hour. If the email has not arrived after 5 minutes, check spam.
"""

state = {
    "next_id": 1000,
    "tickets": {
        "AUTH-88": {"title": "Throttle repeated failed sign-ins", "status": "in code review",
                    "description": AUTH_88, "attachments": [], "comments": [
                        {"author": "priya", "at": "2026-11-03T10:12:00+00:00",
                         "body": "Picked up. MR !231."}]},
        "AUTH-91": {"title": "Faster password reset emails", "status": "open",
                    "description": AUTH_91, "attachments": [], "comments": []},
    },
    "pages": {
        "security/login-throttling": {"title": "Sign-in lockouts (support)", "body": WIKI_THROTTLING,
                                      "attachments": []},
        "security/password-reset": {"title": "Password reset (support)", "body": WIKI_RESET,
                                    "attachments": []},
    },
}
for out in ("/var/lib/fakes/state.json", "/opt/fakes-base/state.json"):
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(json.dumps(state, indent=2))
