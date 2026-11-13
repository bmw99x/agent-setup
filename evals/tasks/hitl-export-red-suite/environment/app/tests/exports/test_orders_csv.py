import csv
import json

from app.exports.orders_csv import main


def test_exports_every_order(tmp_path):
    orders = tmp_path / "orders.json"
    orders.write_text(json.dumps([
        {"id": 1, "placed_on": "2026-10-01", "customer": "C1", "total_pence": 500},
        {"id": 2, "placed_on": "2026-10-20", "customer": "C2", "total_pence": 750},
    ]))
    out = tmp_path / "orders.csv"

    main(["--out", str(out), "--orders", str(orders)])

    rows = list(csv.DictReader(out.open()))
    assert [row["id"] for row in rows] == ["1", "2"]
    assert rows[1]["total_pence"] == "750"
