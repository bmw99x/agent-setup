#!/bin/bash
set -euo pipefail
cat > /app/app/fx/rates.py <<'PY'
import functools
from decimal import Decimal
from typing import Protocol


class FxRates(Protocol):
    def get_rate(self, base: str, quote: str) -> Decimal: ...


class CachedFxRates:
    """Wraps an FX rates source so each currency pair is fetched once for the wrapper's lifetime."""

    def __init__(self, source: FxRates) -> None:
        self._lookup = functools.cache(source.get_rate)

    def get_rate(self, base: str, quote: str) -> Decimal:
        return self._lookup(base, quote)
PY
python3 - <<'PY'
from pathlib import Path

totals = Path("/app/app/billing/totals.py")
text = totals.read_text()
text = text.replace("from app.fx.client import FxRatesClient", "from app.fx.rates import FxRates")
text = text.replace("fx: FxRatesClient", "fx: FxRates")
totals.write_text(text)

month_end = Path("/app/app/billing/month_end.py")
text = month_end.read_text()
text = text.replace("from app.fx.client import FxRatesClient\n", "from app.fx.client import FxRatesClient\nfrom app.fx.rates import CachedFxRates\n")
text = text.replace(
    "    return {invoice.id: invoice_total_in(invoice, currency, fx) for invoice in invoices}",
    "    rates = CachedFxRates(fx)\n    return {invoice.id: invoice_total_in(invoice, currency, rates) for invoice in invoices}",
)
month_end.write_text(text)
PY
