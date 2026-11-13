#!/bin/bash
set -euo pipefail
cd /app

python3 - <<'PY'
from pathlib import Path

p = Path("app/orders/states.py")
t = p.read_text()
t = t.replace(
    "    #: Placed at checkout; waits for the payment provider's webhook. Cancelled after 30 minutes unpaid.\n"
    '    PENDING_PAYMENT = "pending_payment"\n',
    "",
)
t = t.replace("    #: Payment captured; ready for the warehouse.\n", "    #: Placed at checkout with the card authorised; ready for the warehouse.\n")
t = t.replace("INITIAL_STATUS = OrderStatus.PENDING_PAYMENT", "INITIAL_STATUS = OrderStatus.PAID")
t = t.replace("    OrderStatus.PENDING_PAYMENT: frozenset({OrderStatus.PAID, OrderStatus.CANCELLED}),\n", "")
t = t.replace(
    '"""Create an order at checkout. It starts in ``PENDING_PAYMENT`` until the payment webhook lands."""',
    '"""Create an order at checkout. Payment is authorised synchronously, so it starts ``PAID``."""',
)
p.write_text(t)

p = Path("tests/test_states.py")
t = p.read_text().replace(
    'def test_new_order_waits_for_payment():\n    """A new order starts in PENDING_PAYMENT until the payment webhook arrives."""\n'
    "    assert place_order(\"o-1\", NOW).status is OrderStatus.PENDING_PAYMENT\n",
    'def test_new_order_starts_paid():\n    """Payment is authorised at checkout, so a new order starts PAID."""\n'
    "    assert place_order(\"o-1\", NOW).status is OrderStatus.PAID\n",
).replace("    order.transition_to(OrderStatus.PAID)\n", "").replace(
    "    for status in (OrderStatus.PAID, OrderStatus.PACKED):\n        order.transition_to(status)\n",
    "    order.transition_to(OrderStatus.PACKED)\n",
)
p.write_text(t)

p = Path("docs/diagrams/order-lifecycle.dot")
p.write_text("""digraph order_lifecycle {
    rankdir=LR;
    node [shape=box, style=rounded, fontname="Helvetica"];

    start [shape=point];
    PAID; PACKED; SHIPPED; DELIVERED; CANCELLED;

    start -> PAID [label="checkout (card authorised)"];
    PAID -> PACKED [label="packed"];
    PAID -> CANCELLED [label="customer cancels"];
    PACKED -> SHIPPED [label="carrier pickup"];
    SHIPPED -> DELIVERED [label="delivery scan"];
}
""")

p = Path("docs/design/order-lifecycle.md")
t = p.read_text().replace(
    "Status: approved (2026-10-20).\n",
    """Status: approved (2026-10-20).

> **Amended after MR review (2026-11-12).** `PENDING_PAYMENT` and the unpaid-order sweeper were
> removed: payments-service v3 authorises the card at checkout, so new orders start in `PAID`.
> The diagram is re-rendered. Cancellation rules and fulfilment states are unchanged.
""",
).replace(
    "## Unpaid orders\n",
    "## Unpaid orders\n\n> **Superseded.** Removed with `PENDING_PAYMENT`; kept for the reasoning.\n\n",
).replace(
    "- `PENDING_PAYMENT` — created at checkout.",
    "- ~~`PENDING_PAYMENT`~~ (superseded, removed) — created at checkout.",
)
p.write_text(t)
PY
git rm -q app/orders/payment_timeout.py tests/test_payment_timeout.py
make diagrams

TURL=$(tracker attach SHOP-310 docs/diagrams/order-lifecycle.svg)
WURL=$(wiki attach engineering/order-lifecycle docs/diagrams/order-lifecycle.svg)

tracker show SHOP-310 --json | python3 -c '
import json, sys
url = sys.argv[1]
d = json.load(sys.stdin)["description"]
old = "https://tracker.example.test/attachments/a-1001/order-lifecycle.svg"
d = d.replace(old, url)
d = d.replace("## What\n", "## What\n\n> **Amended after MR review (2026-11-12).** `PENDING_PAYMENT` and the 30-minute sweeper were removed: payments-service v3 authorises at checkout, so new orders start in `PAID`. Diagram re-rendered. Rest of the lifecycle unchanged.\n", 1)
d = d.replace("- New orders start in `PENDING_PAYMENT` and wait for the payment provider\x27s webhook.", "- ~~New orders start in `PENDING_PAYMENT` and wait for the payment provider\x27s webhook.~~ New orders start in `PAID`.")
d = d.replace("- Unpaid orders are cancelled by a sweeper after 30 minutes.", "- ~~Unpaid orders are cancelled by a sweeper after 30 minutes.~~ (removed)")
d = d.replace("- [ ] New orders start in `PENDING_PAYMENT`", "- [ ] ~~New orders start in `PENDING_PAYMENT`~~ New orders start in `PAID`")
d = d.replace("- [ ] `PENDING_PAYMENT` orders older than 30 minutes are cancelled automatically", "- [ ] ~~`PENDING_PAYMENT` orders older than 30 minutes are cancelled automatically~~ (removed)")
open("/tmp/shop-310.md", "w").write(d)
' "$TURL"
tracker update SHOP-310 --description-file /tmp/shop-310.md

wiki show engineering/order-lifecycle >/dev/null
python3 - "$WURL" <<'PY'
import json, sys
url = sys.argv[1]
body = json.load(open("/var/lib/fakes/state.json"))["pages"]["engineering/order-lifecycle"]["body"]
body = body.replace("https://wiki.example.test/attachments/a-1002/order-lifecycle.svg", url)
body = body.replace(
    "| `PENDING_PAYMENT` | Order placed, waiting for the payment provider. Cancelled after 30 minutes unpaid. |\n", ""
)
body = body.replace("| `PAID` | Payment captured; ready for the warehouse. |",
                    "| `PAID` | Initial status: placed at checkout with the card authorised; ready for the warehouse. |")
body = body.replace("Ticket: SHOP-310.\n", "Ticket: SHOP-310.\n\n> **Amended (2026-11-12):** `PENDING_PAYMENT` was removed; new orders start in `PAID`.\n")
open("/tmp/wiki.md", "w").write(body)
PY
wiki edit engineering/order-lifecycle --file /tmp/wiki.md
