import json
from pathlib import Path


def ticket(title, status, description, comments=()):
    return {"title": title, "status": status, "description": description, "links": [],
            "comments": [{"author": a, "at": at, "body": b} for a, at, b in comments]}


state = {
    "host": "gitlab.example.test",
    "repo": "shop/shipping",
    "web": "https://gitlab.example.test/shop/shipping",
    "bare": "/srv/git/shop/shipping.git",
    "mr_url": "https://gitlab.example.test/shop/shipping/-/merge_requests/{n}",
    "next_mr": 57,
    "mrs": [],
    "tracker_url": "https://tracker.example.test/browse",
    "statuses": ["Open", "In progress", "In code review", "In review", "Done"],
    "tickets": {
        "SHIP-101": ticket("Show carrier quotes at checkout", "Done",
                           "Fetch a quote from every configured carrier and show them at checkout."),
        "SHIP-118": ticket("Checkout crashes when a carrier times out", "Done",
                           "A single carrier timeout raises and the whole quote step fails. Skip that carrier instead."),
        "SHIP-120": ticket("Cache carrier quotes for 10 minutes", "Open",
                           "Quotes for the same basket and postcode are requested repeatedly. Cache them for 10 minutes."),
        "SHIP-142": ticket("Retry carrier quote requests on timeout", "In progress",
                           "A carrier that times out once is dropped from checkout, even though a second request\n"
                           "usually succeeds. Retry timed-out quote requests (max 3 attempts) with backoff.",
                           [("maria", "2026-11-04T09:30:00+00:00", "Picked up on feature/SHIP-142-carrier-quote-retries.")]),
        "SHIP-149": ticket("Show carrier quote prices including VAT", "Open",
                           "Quote prices are shown ex-VAT at checkout. Finance wants them shown including VAT."),
        "SHIP-150": ticket("DPD 503s drop DPD from checkout", "In progress",
                           "During DPD maintenance windows their quote API answers 503 Service Unavailable for a few\n"
                           "seconds. We treat that as a hard failure and DPD disappears from checkout."),
        "SHIP-157": ticket("Checkout shows 'no delivery options' during carrier blips", "Open",
                           "Support reports customers seeing 'no delivery options' at checkout for a few seconds at a\n"
                           "time. Cause: when every carrier quote times out once, checkout has nothing to show.\n\n"
                           "The carrier quote retry work (SHIP-142, branch feature/SHIP-142-carrier-quote-retries)\n"
                           "fixes this; close this ticket when that merges."),
    },
}
for out in ("/var/lib/fakes/state.json", "/opt/fakes-base/state.json"):
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(json.dumps(state, indent=2))
