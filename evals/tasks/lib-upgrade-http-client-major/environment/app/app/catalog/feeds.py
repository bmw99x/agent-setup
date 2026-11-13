import csv
import io
from decimal import Decimal

from app.http import supplier_client


def download_price_feed() -> dict[str, Decimal]:
    """SKU -> list price from the supplier's nightly CSV feed.

    The supplier generates this file from an old ERP export: it is Windows-1252 encoded and the
    response carries no charset in its Content-Type.
    """
    response = supplier_client().get("/feeds/prices.csv")
    rows = csv.DictReader(io.StringIO(response.text))
    return {row["sku"]: Decimal(row["list_price"]) for row in rows}
