set -e
cd /app
git init -q --bare /srv/git/shop/orders.git
git init -q
git remote add origin git@gitlab.example.test:shop/orders.git
git add -A
git commit -q -m "feat(pricing): order line and order totals"
git commit -q --allow-empty -m "ci: add integration tests against Postgres"
git push -q -u origin main
git remote set-head origin -a >/dev/null
install -m 755 /opt/fakes/update-hook /srv/git/shop/orders.git/hooks/update
git checkout -q -b feature/bulk-discount

cat > orders/discounts.py <<'PY'
"""Bulk discounts on order lines."""

import math
from decimal import Decimal

BULK_THRESHOLD = 10
BULK_RATE = Decimal("0.10")


def bulk_discount(quantity: int, unit_price: Decimal) -> Decimal:
    """10% off a line once it reaches BULK_THRESHOLD (10) items or more."""
    if quantity > BULK_THRESHOLD:
        return (unit_price * quantity * BULK_RATE).quantize(Decimal("0.01"))
    return Decimal("0.00")
PY
python3 - <<'PY'
from pathlib import Path
p = Path("orders/pricing.py")
s = p.read_text()
s = s.replace("from decimal import Decimal\n", "from decimal import Decimal\n\nfrom orders.discounts import bulk_discount\n")
s = s.replace("    return (line.unit_price * line.quantity).quantize(Decimal(\"0.01\"))\n",
              "    gross = (line.unit_price * line.quantity).quantize(Decimal(\"0.01\"))\n"
              "    return gross - bulk_discount(line.quantity, line.unit_price)\n")
p.write_text(s)
PY
cat > tests/unit/test_discounts.py <<'PY'
from decimal import Decimal

from orders.discounts import bulk_discount
from orders.pricing import OrderLine, line_total


def test_no_discount_below_ten_items():
    assert bulk_discount(9, Decimal("5.00")) == Decimal("0.00")


def test_line_total_applies_bulk_discount():
    assert line_total(OrderLine("A-1", 12, Decimal("2.00"))) == Decimal("21.60")
PY
git add orders/discounts.py orders/pricing.py tests/unit/test_discounts.py
git commit -q -m "feat(discounts): 10% off order lines of 10 or more items"
cat >> tests/unit/test_discounts.py <<'PY'


def test_bulk_discount_starts_at_ten_items():
    assert bulk_discount(10, Decimal("5.00")) == Decimal("5.00")
PY
git add tests/unit/test_discounts.py
git commit -q -m "test(discounts): cover the ten-item threshold"
git push -q -u origin feature/bulk-discount

# The developer's uncommitted, unrelated work in progress.
cat >> README.md <<'MD'

## Discounts

Order lines of 10 or more items get 10% off. TODO: explain how this stacks with voucher codes.
MD
