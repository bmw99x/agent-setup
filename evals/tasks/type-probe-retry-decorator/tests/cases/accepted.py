from collections.abc import Sequence
from decimal import Decimal

from app.rates.conversion import convert_from_eur
from app.rates.ecb_client import EcbRateClient
from app.rates.source import RateSource
from app.rates.transport import Transport
from app.retry import retry


class FixedRates:
    @retry(attempts=2)
    async def fetch_rate(self, currency: str) -> Decimal:
        return Decimal("1")

    @retry(attempts=2)
    async def fetch_rates(self, currencies: Sequence[str]) -> dict[str, Decimal]:
        return {currency: Decimal("1") for currency in currencies}


@retry(attempts=4)
async def lookup(code: str, *, scale: int = 2) -> list[int]:
    return [scale]


def use_source(source: RateSource) -> None: ...


async def main(transport: Transport) -> None:
    client = EcbRateClient(transport)
    use_source(client)
    use_source(FixedRates())
    rate: Decimal = await client.fetch_rate("USD")
    rates: dict[str, Decimal] = await client.fetch_rates(["USD", "GBP"])
    converted: Decimal = await convert_from_eur(Decimal("2"), "USD", client)
    values: list[int] = await lookup("x", scale=3)
