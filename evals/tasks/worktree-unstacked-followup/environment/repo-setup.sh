set -e
git init -q --bare /app/origin.git
cd /app/repo
git init -q
git remote add origin /app/origin.git
git add .
git commit -q -m "feat: add orders"
git push -q -u origin main

# Discounts: committed, pushed, MR open, not merged.
git checkout -q -b feat/order-discounts
cat > billing/discounts.py <<'PY'
from decimal import Decimal


def percentage_discount(amount: Decimal, percent: int) -> Decimal:
    return (amount * Decimal(100 - percent) / Decimal(100)).quantize(Decimal("0.01"))
PY
git add billing/discounts.py
git commit -q -m "feat(discounts): add percentage discount"
cat > tests/test_discounts.py <<'PY'
from decimal import Decimal

from billing.discounts import percentage_discount


def test_ten_percent_off():
    assert percentage_discount(Decimal("20.00"), 10) == Decimal("18.00")
PY
git add tests/test_discounts.py
git commit -q -m "test(discounts): cover percentage discount"
git push -q -u origin feat/order-discounts
