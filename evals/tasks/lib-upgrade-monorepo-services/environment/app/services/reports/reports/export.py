import csv
import io

from ledgerkit import Money
from ledgerkit.formats import format_money


def revenue_csv(by_region: dict[str, Money]) -> str:
    """CSV for the Frankfurt finance team, who want German number formatting."""
    out = io.StringIO()
    writer = csv.writer(out, delimiter=";")
    writer.writerow(["region", "revenue"])
    for region, revenue in sorted(by_region.items()):
        writer.writerow([region, format_money(revenue, "de_DE")])
    return out.getvalue()
