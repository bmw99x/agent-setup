from collections import defaultdict
from datetime import date

from app.reports import repository


def build_sales_report(
    start: date,
    end: date,
    region: str | None,
    currency: str,
    include_refunds: bool,
    group_by: str,
    top_n: int | None,
) -> list[tuple[str, int]]:
    totals: dict[str, int] = defaultdict(int)
    for sale in repository.sales_between(start, end):
        if sale.currency != currency:
            continue
        if region is not None and sale.region != region:
            continue
        if sale.is_refund and not include_refunds:
            continue
        totals[getattr(sale, group_by)] += sale.amount_pence
    ranked = sorted(totals.items(), key=lambda item: (-item[1], item[0]))
    return ranked[:top_n] if top_n is not None else ranked
