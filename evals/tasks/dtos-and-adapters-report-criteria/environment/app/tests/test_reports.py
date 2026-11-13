from datetime import date

from app.reports.api import get_sales_report
from app.reports.jobs import weekly_product_export
from app.reports.schemas import SalesReportRequest


def test_sales_report_groups_by_region():
    request = SalesReportRequest.model_validate({"start": "2026-03-01", "end": "2026-03-07"})
    response = get_sales_report(request)
    assert [(row.key, row.total_pence) for row in response.rows] == [("north", 5_500), ("south", 2_000)]


def test_weekly_export_includes_refunds():
    csv_text = weekly_product_export(date(2026, 3, 7))
    assert csv_text.splitlines() == ["product,total_pence", "toaster,3500", "kettle,2000"]
