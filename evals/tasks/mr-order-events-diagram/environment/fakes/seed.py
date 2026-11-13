import json
from pathlib import Path


def ticket(title, status, description, comments=()):
    return {"title": title, "status": status, "description": description, "links": [],
            "comments": [{"author": a, "at": at, "body": b} for a, at, b in comments]}


state = {
    "host": "gitlab.example.test",
    "repo": "shop/orders",
    "web": "https://gitlab.example.test/shop/orders",
    "bare": "/srv/git/shop/orders.git",
    "mr_url": "https://gitlab.example.test/shop/orders/-/merge_requests/{n}",
    "next_mr": 212,
    "mrs": [],
    "tracker_url": "https://tracker.example.test/browse",
    "statuses": ["Open", "In progress", "In code review", "In review", "Done"],
    "tickets": {
        "ORD-61": ticket("Place orders through a single checkout entry point", "Done",
                         "Move order placement into orders.checkout.place_order."),
        "ORD-77": ticket("Send order confirmations asynchronously", "In progress",
                         "## Why\n"
                         "Incident INC-2291 (28 Oct): notifications-service slowed to ~8 s per request and checkout\n"
                         "timed out for 40 minutes, because place_order calls it synchronously to send the\n"
                         "confirmation email. Orders were lost.\n\n"
                         "## What\n"
                         "place_order publishes an `order.placed` event to the `order-events` queue instead of\n"
                         "calling notifications-service. notifications-service consumes the event and sends the\n"
                         "confirmation email. Checkout no longer depends on notifications-service being up.\n",
                         [("sam", "2026-11-05T14:02:00+00:00",
                           "Consumer side is in notifications-service: "
                           "https://gitlab.example.test/shop/notifications/-/merge_requests/88\n"
                           "That one has to be deployed before the orders change, otherwise confirmation "
                           "emails stop until it is.")]),
        "ORD-80": ticket("Paginate order history", "Open",
                         "The order history endpoint returns every order a customer ever placed. Paginate it."),
    },
}
for out in ("/var/lib/fakes/state.json", "/opt/fakes-base/state.json"):
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(json.dumps(state, indent=2))
