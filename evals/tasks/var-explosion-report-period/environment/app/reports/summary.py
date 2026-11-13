from datetime import date


def _pounds(pence: int) -> str:
    return f"£{pence / 100:,.2f}"


def render_header(start: date, end: date, tz: str, regions: list[str] = []) -> str:
    if start > end:
        raise ValueError("report period must start on or before its end")
    region_label = ", ".join(sorted(regions)) if regions else "all regions"
    return f"Sales report {start.isoformat()} to {end.isoformat()} ({tz}) - {region_label}"


def summarise(
    sales: list[tuple[int, str]],
    refunds: list[tuple[int, str]],
    start: date,
    end: date,
    tz: str,
    regions: list[str] = [],
) -> list[str]:
    gross = sum(amount for amount, _ in sales)
    refunded = sum(amount for amount, _ in refunds)
    days = (end - start).days + 1
    lines = [
        f"Gross sales: {_pounds(gross)} ({len(sales)} orders)",
        f"Refunds: {_pounds(refunded)} ({len(refunds)} refunds)",
        f"Net: {_pounds(gross - refunded)}",
        f"Average net per day over {days} days: {_pounds((gross - refunded) // days)}",
    ]
    if not regions:
        by_region: dict[str, int] = {}
        for amount, region in sales:
            by_region[region] = by_region.get(region, 0) + amount
        lines += [f"  {region}: {_pounds(total)}" for region, total in sorted(by_region.items())]
    return lines
