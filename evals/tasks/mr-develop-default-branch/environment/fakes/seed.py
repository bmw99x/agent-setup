import json
from pathlib import Path


def ticket(title, status, description, comments=()):
    return {"title": title, "status": status, "description": description, "links": [],
            "comments": [{"author": a, "at": at, "body": b} for a, at, b in comments]}


state = {
    "host": "github.com",
    "repo": "acme-test/accounts",
    "web": "https://github.com/acme-test/accounts",
    "bare": "/srv/git/acme-test/accounts.git",
    "mr_url": "https://github.com/acme-test/accounts/pull/{n}",
    "next_mr": 342,
    "mrs": [],
    "tracker_url": "https://tracker.example.test/browse",
    "statuses": ["Open", "In progress", "In code review", "In review", "Done"],
    "tickets": {
        "ACC-50": ticket("Sliding session expiry", "Done", "Extend a session's expiry on every request."),
        "ACC-58": ticket("Set SameSite=Lax on the session cookie", "In progress",
                         "Browsers warn that the session cookie has no SameSite attribute. Set SameSite=Lax."),
        "ACC-61": ticket("Sessions expire early for users east of UTC", "In progress",
                         "Users in Asia/Tokyo report being signed out hours early. Session expiry is compared\n"
                         "against the server's local wall-clock time instead of UTC."),
    },
}
for out in ("/var/lib/fakes/state.json", "/opt/fakes-base/state.json"):
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(json.dumps(state, indent=2))
