import asyncio
from decimal import Decimal

import pytest

from app.errors import TransientError
from app.rates.ecb_client import EcbRateClient
from app.rates.pricing import price_in


class FlakyTransport:
    def __init__(self, failures: int) -> None:
        self.failures = failures
        self.calls = 0

    async def get_json(self, path: str) -> dict[str, str]:
        self.calls += 1
        if self.calls <= self.failures:
            raise TransientError(path)
        return {"rate": "1.10", "USD": "1.10", "GBP": "0.85"}


def test_fetch_rate_retries_transient_failures() -> None:
    transport = FlakyTransport(failures=2)

    rate = asyncio.run(EcbRateClient(transport).fetch_rate("USD"))

    assert rate == Decimal("1.10")
    assert transport.calls == 3


def test_fetch_rates_gives_up_after_three_attempts() -> None:
    transport = FlakyTransport(failures=3)

    with pytest.raises(TransientError):
        asyncio.run(EcbRateClient(transport).fetch_rates(["USD", "GBP"]))
    assert transport.calls == 3


def test_price_in_converts_from_eur() -> None:
    price = asyncio.run(price_in("USD", Decimal("10"), FlakyTransport(failures=0)))

    assert price == Decimal("11.00")
