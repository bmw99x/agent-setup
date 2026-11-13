"""VAT rules."""

from decimal import ROUND_HALF_UP, Decimal

VAT_RATES = {"GB": Decimal("0.20"), "DE": Decimal("0.19"), "FR": Decimal("0.20"), "IE": Decimal("0.23")}


class UnknownCountry(Exception):
    pass


def compute_vat(net_cents, country):
    """VAT owed on a net amount, in cents, rounded half-up."""
    try:
        rate = VAT_RATES[country]
    except KeyError as exc:
        raise UnknownCountry(country) from exc
    return int((Decimal(net_cents) * rate).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
