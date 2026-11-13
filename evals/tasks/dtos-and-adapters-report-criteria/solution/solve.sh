#!/bin/bash
cat > /app/app/reports/dtos.py <<'PY'
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class SalesReportCriteria:
    start: date
    end: date
    currency: str
    group_by: str
    region: str | None = None
    include_refunds: bool = False
    top_n: int | None = None
PY
cat > /app/app/reports/service.py <<'PY'
from collections import defaultdict

from app.reports import repository
from app.reports.dtos import SalesReportCriteria


def build_sales_report(criteria: SalesReportCriteria) -> list[tuple[str, int]]:
    totals: dict[str, int] = defaultdict(int)
    for sale in repository.sales_between(criteria.start, criteria.end):
        if sale.currency != criteria.currency:
            continue
        if criteria.region is not None and sale.region != criteria.region:
            continue
        if sale.is_refund and not criteria.include_refunds:
            continue
        totals[getattr(sale, criteria.group_by)] += sale.amount_pence
    ranked = sorted(totals.items(), key=lambda item: (-item[1], item[0]))
    return ranked[: criteria.top_n] if criteria.top_n is not None else ranked
PY
cat > /app/app/reports/api.py <<'PY'
from app.reports.dtos import SalesReportCriteria
from app.reports.schemas import SalesReportRequest, SalesReportResponse, SalesReportRow
from app.reports.service import build_sales_report


def get_sales_report(request: SalesReportRequest) -> SalesReportResponse:
    criteria = SalesReportCriteria(
        start=request.start,
        end=request.end,
        region=request.region,
        currency=request.currency,
        include_refunds=request.include_refunds,
        group_by=request.group_by,
        top_n=request.top_n,
    )
    rows = build_sales_report(criteria)
    return SalesReportResponse(
        currency=request.currency,
        rows=[SalesReportRow(key=key, total_pence=total) for key, total in rows],
    )
PY
cat > /app/app/reports/jobs.py <<'PY'
import csv
import io
from datetime import date, timedelta

from app.reports.dtos import SalesReportCriteria
from app.reports.service import build_sales_report


def weekly_product_export(week_ending: date) -> str:
    """CSV of the week's top products, uploaded by the nightly scheduler."""
    criteria = SalesReportCriteria(
        start=week_ending - timedelta(days=6),
        end=week_ending,
        currency="GBP",
        include_refunds=True,
        group_by="product",
        top_n=10,
    )
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["product", "total_pence"])
    writer.writerows(build_sales_report(criteria))
    return buffer.getvalue()
PY
