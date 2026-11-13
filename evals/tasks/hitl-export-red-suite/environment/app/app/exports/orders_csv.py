"""Orders CSV export for finance.

    python -m app.exports.orders_csv --out orders.csv [--orders var/orders.json]
"""
import argparse
import csv
import json
from pathlib import Path

ORDERS_FILE = Path(__file__).resolve().parents[2] / "var" / "orders.json"
COLUMNS = ("id", "placed_on", "customer", "total_pence")


def load_orders(path: Path) -> list[dict]:
    return json.loads(path.read_text())


def write_csv(orders: list[dict], out: Path) -> None:
    with out.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(orders)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Export orders as CSV for finance.")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--orders", type=Path, default=ORDERS_FILE)
    args = parser.parse_args(argv)
    write_csv(load_orders(args.orders), args.out)


if __name__ == "__main__":
    main()
