from ledgerkit import Money


def monthly_revenue(rows: list[dict]) -> Money:
    """Rows come from the warehouse export, where amounts are floats."""
    total = Money.from_float(0.0, "GBP")
    for row in rows:
        total = total + Money.from_float(row["amount"], "GBP")
    return total.round()
