from decimal import Decimal

from app.rates.source import RateSource


async def convert_from_eur(amount: Decimal, currency: str, source: RateSource) -> Decimal:
    return amount * await source.fetch_rate(currency)
