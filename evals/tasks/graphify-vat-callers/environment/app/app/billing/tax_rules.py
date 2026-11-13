"""Tax rule per invoice tax kind."""

from app.billing.tax import compute_vat


def _zero_rated(net_cents, country):
    return 0


TAX_RULES = {
    "VAT": compute_vat,
    "REVERSE_CHARGE": _zero_rated,
    "EXPORT": _zero_rated,
}
