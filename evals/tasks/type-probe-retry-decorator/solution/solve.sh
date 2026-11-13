#!/bin/bash
set -euo pipefail
cat > /app/app/retry.py <<'PY'
import functools
from collections.abc import Callable, Coroutine
from typing import Any

from app.errors import TransientError

type AsyncCall[**P, R] = Callable[P, Coroutine[Any, Any, R]]


def retry[**P, R](*, attempts: int) -> Callable[[AsyncCall[P, R]], AsyncCall[P, R]]:
    """Re-run the call on TransientError, up to `attempts` calls in total, then re-raise."""

    def decorate(call: AsyncCall[P, R]) -> AsyncCall[P, R]:
        @functools.wraps(call)
        async def with_retries(*args: P.args, **kwargs: P.kwargs) -> R:
            for attempt in range(1, attempts):
                try:
                    return await call(*args, **kwargs)
                except TransientError:
                    continue
            return await call(*args, **kwargs)

        return with_retries

    return decorate
PY
cat > /app/app/rates/ecb_client.py <<'PY'
from collections.abc import Sequence
from decimal import Decimal

from app.rates.transport import Transport
from app.retry import retry

ATTEMPTS = 3


class EcbRateClient:
    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    @retry(attempts=ATTEMPTS)
    async def fetch_rate(self, currency: str) -> Decimal:
        payload = await self._transport.get_json(f"/rates/{currency}")
        return Decimal(payload["rate"])

    @retry(attempts=ATTEMPTS)
    async def fetch_rates(self, currencies: Sequence[str]) -> dict[str, Decimal]:
        payload = await self._transport.get_json(f"/rates?symbols={','.join(currencies)}")
        return {currency: Decimal(payload[currency]) for currency in currencies}
PY
