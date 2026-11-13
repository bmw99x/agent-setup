"""VAT rates applied to checkout quotes."""

from decimal import Decimal

VAT_RATES = {
    "GB": Decimal("0.20"),
    "IE": Decimal("0.23"),
    "FR": Decimal("0.20"),
    "DE": Decimal("0.19"),
    "ES": Decimal("0.21"),
    "PT": Decimal("0.23"),
}

# Regions taxed differently from the rest of their country, keyed by ISO 3166-2 subdivision.
REGIONAL_RATES = {
    ("ES", "CN"): Decimal("0.07"),  # Canary Islands (IGIC)
    ("PT", "30"): Decimal("0.22"),  # Madeira
}


def vat_rate(country: str, region: str | None = None) -> Decimal:
    if region:
        return REGIONAL_RATES[(country, region)]
    return VAT_RATES[country]
