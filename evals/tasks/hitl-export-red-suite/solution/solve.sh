#!/bin/bash
set -euo pipefail
cd /app
python3 - <<'PY'
from pathlib import Path

path = Path("app/exports/orders_csv.py")
source = path.read_text()
source = source.replace("import json\n", "import json\nfrom datetime import date\n")
source = source.replace(
    "    --out orders.csv [--orders var/orders.json]\n",
    "    --out orders.csv [--orders var/orders.json] [--since YYYY-MM-DD]\n",
)
source = source.replace(
    "def write_csv(",
    "def placed_since(orders: list[dict], since: date) -> list[dict]:\n"
    "    # ASSUMPTION: \"since\" is inclusive - an order placed on the --since date is exported.\n"
    "    return [order for order in orders if date.fromisoformat(order[\"placed_on\"]) >= since]\n\n\n"
    "def write_csv(",
)
source = source.replace(
    "    args = parser.parse_args(argv)\n    write_csv(load_orders(args.orders), args.out)\n",
    "    parser.add_argument(\"--since\", type=date.fromisoformat, help=\"only orders placed on or after YYYY-MM-DD\")\n"
    "    args = parser.parse_args(argv)\n"
    "    orders = load_orders(args.orders)\n"
    "    if args.since is not None:\n"
    "        orders = placed_since(orders, args.since)\n"
    "    write_csv(orders, args.out)\n",
)
path.write_text(source)
PY
cat > HANDOFF.md <<'MD'
# Handoff

## Done
- `--since YYYY-MM-DD` on `python -m app.exports.orders_csv` (inclusive of that date).

## Blocked: suite is red because of the partner feed, not the export
`tests/partner_feed/test_feed.py::test_feed_item_carries_price_in_pence` fails. Priya's WIP commit
("expect Shopwise v3 item format") changed the test to `price_pence` + `currency`, but
`app/partner_feed/feed.py` still emits the v2 `price: "12.50"`. Changing the feed changes what we
send to Shopwise, which belongs to the partnerships team, so I left both files alone.
Should Priya finish the v3 switch, or should the test go back to v2 until Shopwise cuts over?
MD
