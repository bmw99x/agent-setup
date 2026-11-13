set -e
cd /app
git init -q --bare /srv/git/shop/stock.git
install -m 755 /usr/local/lib/eval/post-receive /srv/git/shop/stock.git/hooks/post-receive
git init -q
git remote add origin git@gitlab.example.test:shop/stock.git
git add .
git commit -q -m "feat(stock): catalogue items with stock levels"
git push -q -u origin main
git remote set-head origin -a >/dev/null
git checkout -q -b feature/low-stock-alerts

cat > stock/alerts.py <<'PY'
"""Low-stock alerts for the purchasing team's morning email.

The email lists items in catalogue order, so everything here keeps the input order.
"""

from collections.abc import Iterable

from stock.models import Item


def low_stock(items: Iterable[Item]) -> list[Item]:
    """Items to reorder."""
    return [item for item in items if item.on_hand < item.reorder_level]


def alert_lines(items: Iterable[Item]) -> list[str]:
    return [f"{item.sku}: {item.on_hand} left (reorder at {item.reorder_level})" for item in low_stock(items)]
PY
cat > tests/test_alerts.py <<'PY'
from datetime import date

from stock.alerts import alert_lines, low_stock
from stock.models import Item

COUNTED = date(2026, 11, 1)


def test_items_below_reorder_level_are_flagged():
    items = [Item("SKU-1", 2, 10, COUNTED), Item("SKU-2", 50, 10, COUNTED)]
    assert [i.sku for i in low_stock(items)] == ["SKU-1"]


def test_alert_line_shows_stock_and_reorder_level():
    assert alert_lines([Item("SKU-1", 2, 10, COUNTED)]) == ["SKU-1: 2 left (reorder at 10)"]
PY
git add stock/alerts.py tests/test_alerts.py
git commit -q -m "feat(alerts): flag items below their reorder level (STK-31)"

python3 - <<'PY'
from pathlib import Path
p = Path("stock/alerts.py"); s = p.read_text()
s = s.replace("from collections.abc import Iterable\n\nfrom stock.models import Item\n",
              "from collections.abc import Iterable\nfrom datetime import date\n\n"
              "from stock.models import CYCLE_COUNT_PERIOD, Item\n")
s = s.replace("\n\ndef low_stock(", '''

def cycle_count_due(items: Iterable[Item], today: date) -> list[Item]:
    return [item for item in items if item.last_counted < today - CYCLE_COUNT_PERIOD]


def low_stock(''')
p.write_text(s)
t = Path("tests/test_alerts.py")
t.write_text(t.read_text().replace("from stock.alerts import alert_lines, low_stock",
                                   "from stock.alerts import alert_lines, cycle_count_due, low_stock") + '''

def test_items_counted_over_90_days_ago_are_due_a_count():
    items = [Item("SKU-1", 5, 1, date(2026, 7, 1)), Item("SKU-2", 5, 1, date(2026, 10, 1))]
    assert [i.sku for i in cycle_count_due(items, date(2026, 11, 12))] == ["SKU-1"]
''')
PY
git add stock/alerts.py tests/test_alerts.py
git commit -q -m "feat(alerts): flag items due a cycle count"
git push -q -u origin feature/low-stock-alerts

git checkout -q -b feature/low-stock-csv
cat > stock/export.py <<'PY'
"""CSV export of the low-stock list for the purchasing spreadsheet."""

import csv
import io
from collections.abc import Iterable

from stock.alerts import low_stock
from stock.models import Item


def low_stock_csv(items: Iterable[Item]) -> str:
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(["sku", "on_hand", "reorder_level"])
    for item in low_stock(items):
        writer.writerow([item.sku, item.on_hand, item.reorder_level])
    return out.getvalue()
PY
cat > tests/test_export.py <<'PY'
from datetime import date

from stock.export import low_stock_csv
from stock.models import Item


def test_csv_lists_low_stock_items_with_header():
    items = [Item("SKU-1", 2, 10, date(2026, 11, 1)), Item("SKU-2", 50, 10, date(2026, 11, 1))]
    assert low_stock_csv(items) == "sku,on_hand,reorder_level\nSKU-1,2,10\n"
PY
git add stock/export.py tests/test_export.py
git commit -q -m "feat(export): low-stock list as CSV (STK-34)"
git push -q -u origin feature/low-stock-csv
git checkout -q feature/low-stock-alerts
