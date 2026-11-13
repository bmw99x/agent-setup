from app.reports.schemas import SalesReportRequest, SalesReportResponse, SalesReportRow
from app.reports.service import build_sales_report


def get_sales_report(request: SalesReportRequest) -> SalesReportResponse:
    rows = build_sales_report(
        start=request.start,
        end=request.end,
        region=request.region,
        currency=request.currency,
        include_refunds=request.include_refunds,
        group_by=request.group_by,
        top_n=request.top_n,
    )
    return SalesReportResponse(
        currency=request.currency,
        rows=[SalesReportRow(key=key, total_pence=total) for key, total in rows],
    )
