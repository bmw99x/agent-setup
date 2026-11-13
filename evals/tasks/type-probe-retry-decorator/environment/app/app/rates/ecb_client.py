from collections.abc import Sequence
from decimal import Decimal

from app.errors import TransientError
from app.rates.transport import Transport

ATTEMPTS = 3


class EcbRateClient:
    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    async def fetch_rate(self, currency: str) -> Decimal:
        for attempt in range(1, ATTEMPTS + 1):
            try:
                payload = await self._transport.get_json(f"/rates/{currency}")
                return Decimal(payload["rate"])
            except TransientError:
                if attempt == ATTEMPTS:
                    raise
        raise AssertionError("unreachable")

    async def fetch_rates(self, currencies: Sequence[str]) -> dict[str, Decimal]:
        for attempt in range(1, ATTEMPTS + 1):
            try:
                payload = await self._transport.get_json(f"/rates?symbols={','.join(currencies)}")
                return {currency: Decimal(payload[currency]) for currency in currencies}
            except TransientError:
                if attempt == ATTEMPTS:
                    raise
        raise AssertionError("unreachable")
