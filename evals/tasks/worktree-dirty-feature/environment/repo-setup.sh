set -e
git init -q --bare /app/origin.git
cd /app/repo
git init -q
git remote add origin /app/origin.git
git add .
git commit -q -m "feat: add stock report"
git push -q -u origin main

# Committed, unmerged CSV export work on its own branch.
git checkout -q -b feat/csv-export
cat > stock/csv_export.py <<'PY'
import csv
import io

from stock.items import Item


def to_csv(items: list[Item]) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["sku", "name", "quantity"])
    for item in items:
        writer.writerow([item.sku, item.name, item.quantity])
    return buffer.getvalue()
PY
git add stock/csv_export.py
git commit -q -m "feat(export): add csv serialiser"
git push -q -u origin feat/csv-export

# Uncommitted work in progress: a staged test, an unstaged edit, an untracked file.
cat > tests/test_csv_export.py <<'PY'
from stock.csv_export import to_csv
from stock.items import Item


def test_to_csv_has_header():
    assert to_csv([Item("A1", "Bolt", 3)]).splitlines()[0] == "sku,name,quantity"
PY
git add tests/test_csv_export.py
cat >> stock/report.py <<'PY'


def format_report_as(items: list[Item], fmt: str = "tsv") -> str:
    # WIP: wire csv export into the report
    if fmt == "csv":
        from stock.csv_export import to_csv

        return to_csv(items)
    return format_report(items)
PY
cat > EXPORT-NOTES.md <<'MD'
WIP notes: decide whether csv export streams or buffers.
MD
