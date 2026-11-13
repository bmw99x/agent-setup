"""VAT summary for the quarterly return, kept from the old finance scripts."""

FLAT_RATE = 0.2


def compute_vat(amount_cents, rate=FLAT_RATE):
    return round(amount_cents * rate)


def vat_summary(conn):
    total_net = conn.execute("SELECT COALESCE(SUM(net_cents), 0) FROM invoices").fetchone()[0]
    return {"netCents": total_net, "estimatedVatCents": compute_vat(total_net)}
