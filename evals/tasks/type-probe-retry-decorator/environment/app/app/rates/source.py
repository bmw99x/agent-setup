from collections.abc import Sequence
from decimal import Decimal
from typing import Protocol


class RateSource(Protocol):
    async def fetch_rate(self, currency: str) -> Decimal:
        """Units of `currency` per 1 EUR."""
        ...

    async def fetch_rates(self, currencies: Sequence[str]) -> dict[str, Decimal]: ...
