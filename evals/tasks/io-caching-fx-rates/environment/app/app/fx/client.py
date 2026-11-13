"""HTTP client for the FX rates provider."""

import json
import urllib.request
from collections.abc import Callable
from decimal import Decimal

HttpGet = Callable[[str], dict]


def _urlopen_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=10) as response:
        return json.load(response)


class FxRatesClient:
    """Fetches exchange rates from the provider. One HTTP request per lookup."""

    def __init__(self, base_url: str, *, http_get: HttpGet = _urlopen_json) -> None:
        self._base_url = base_url.rstrip("/")
        self._http_get = http_get

    def get_rate(self, base: str, quote: str) -> Decimal:
        """Return how many units of `quote` one unit of `base` buys."""
        payload = self._http_get(f"{self._base_url}/rates?base={base}&quote={quote}")
        return Decimal(str(payload["rate"]))
