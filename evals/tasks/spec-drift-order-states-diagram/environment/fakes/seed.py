import json
import shutil
from pathlib import Path

SVG = Path("/app/docs/diagrams/order-lifecycle.svg")
UPLOADS = Path("/var/lib/fakes/uploads")
UPLOADS.mkdir(parents=True, exist_ok=True)
shutil.copyfile(SVG, UPLOADS / "a-1001-order-lifecycle.svg")
shutil.copyfile(SVG, UPLOADS / "a-1002-order-lifecycle.svg")
TRACKER_URL = "https://tracker.example.test/attachments/a-1001/order-lifecycle.svg"
WIKI_URL = "https://wiki.example.test/attachments/a-1002/order-lifecycle.svg"

SHOP_310 = f"""## Why
Orders need an explicit lifecycle so the warehouse, support and the storefront agree on what an
order's status means and which moves are allowed.

## What
Model the order lifecycle as a state machine:

![Order lifecycle]({TRACKER_URL})

- New orders start in `PENDING_PAYMENT` and wait for the payment provider's webhook.
- Unpaid orders are cancelled by a sweeper after 30 minutes.
- `PAID` orders can be packed or cancelled; after `PACKED` an order can no longer be cancelled.

## Acceptance criteria
- [ ] New orders start in `PENDING_PAYMENT`
- [ ] `PENDING_PAYMENT` orders older than 30 minutes are cancelled automatically
- [ ] Invalid transitions raise `InvalidTransition`
- [ ] Lifecycle diagram attached here and on the wiki page `engineering/order-lifecycle`
"""

SHOP_311 = """## Why
Pickers walk too far between zones.

## What
Re-slot fast movers into zone A. Diagram: see `engineering/warehouse-zones` on the wiki.
"""

WIKI_LIFECYCLE = f"""Owner: orders team. Ticket: SHOP-310.

![Order lifecycle]({WIKI_URL})

| Status | Meaning |
|---|---|
| `PENDING_PAYMENT` | Order placed, waiting for the payment provider. Cancelled after 30 minutes unpaid. |
| `PAID` | Payment captured; ready for the warehouse. |
| `PACKED` | Packed; can no longer be cancelled. |
| `SHIPPED` | Handed to the carrier. |
| `DELIVERED` | Carrier confirmed delivery. |
| `CANCELLED` | Cancelled before packing. |
"""

WIKI_WAREHOUSE = """Zones A-D. Fast movers live in zone A next to the packing benches.
"""

state = {
    "next_id": 1002,
    "tickets": {
        "SHOP-310": {"title": "Order lifecycle state machine", "status": "in code review",
                     "description": SHOP_310, "comments": [],
                     "attachments": [{"id": "a-1001", "name": "order-lifecycle.svg", "url": TRACKER_URL,
                                      "stored": str(UPLOADS / "a-1001-order-lifecycle.svg")}]},
        "SHOP-311": {"title": "Re-slot fast movers", "status": "open", "description": SHOP_311,
                     "comments": [], "attachments": []},
    },
    "pages": {
        "engineering/order-lifecycle": {"title": "Order lifecycle", "body": WIKI_LIFECYCLE,
                                        "attachments": [{"id": "a-1002", "name": "order-lifecycle.svg",
                                                         "url": WIKI_URL,
                                                         "stored": str(UPLOADS / "a-1002-order-lifecycle.svg")}]},
        "engineering/warehouse-zones": {"title": "Warehouse zones", "body": WIKI_WAREHOUSE, "attachments": []},
    },
}
for out in ("/var/lib/fakes/state.json", "/opt/fakes-base/state.json"):
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(json.dumps(state, indent=2))
