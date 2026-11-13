import csv
import io
from datetime import date, timedelta

from app.reports.service import build_sales_report


def weekly_product_export(week_ending: date) -> str:
    """CSV of the week's top products, uploaded by the nightly scheduler."""
    rows = build_sales_report(
        start=week_ending - timedelta(days=6),
        end=week_ending,
        region=None,
        currency="GBP",
        include_refunds=True,
        group_by="product",
        top_n=10,
    )
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["product", "total_pence"])
    writer.writerows(rows)
    return buffer.getvalue()
