#!/bin/bash
set -e
cd /app/repo
git worktree add -q /app/low-stock-alerts -b feat/low-stock-alerts main
cd /app/low-stock-alerts
cat > stock/alerts.py <<'PY'
from stock.items import Item


def low_stock(items: list[Item], threshold: int = 5) -> list[Item]:
    return sorted((item for item in items if item.quantity < threshold), key=lambda item: item.quantity)
PY
cat > tests/test_alerts.py <<'PY'
from stock.alerts import low_stock
from stock.items import Item


def test_low_stock_returns_items_below_threshold_lowest_first():
    items = [Item("A", "a", 7), Item("B", "b", 2), Item("C", "c", 0)]
    assert [item.sku for item in low_stock(items)] == ["C", "B"]
PY
python3 -m pytest -q -p no:cacheprovider
git add stock/alerts.py tests/test_alerts.py
git commit -q -m "feat(alerts): add low-stock alert"
