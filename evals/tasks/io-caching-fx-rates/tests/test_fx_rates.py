import ast
import importlib
import sys
from collections import Counter
from decimal import Decimal
from pathlib import Path

import pytest

sys.path.insert(0, "/app")

from app.billing.models import Invoice, InvoiceLine  # noqa: E402
from app.fx.client import FxRatesClient  # noqa: E402

BILLING = Path("/app/app/billing")


class FakeProvider:
    """Stands in for the provider's HTTP endpoint and counts requests per currency pair."""

    def __init__(self, rates: dict[tuple[str, str], str]) -> None:
        self.rates = rates
        self.requests: Counter[tuple[str, str]] = Counter()

    def __call__(self, url: str) -> dict:
        query = dict(part.split("=") for part in url.split("?", 1)[1].split("&"))
        pair = (query["base"], query["quote"])
        self.requests[pair] += 1
        return {"rate": self.rates[pair]}


def _invoices() -> list[Invoice]:
    return [
        Invoice(
            id=f"INV-{n}",
            customer=f"C{n}",
            lines=[
                InvoiceLine("widgets", Decimal("100.00"), "EUR"),
                InvoiceLine("shipping", Decimal("10.00"), "USD"),
                InvoiceLine("fee", Decimal("5.00"), "GBP"),
                InvoiceLine("more widgets", Decimal("20.00"), "EUR"),
            ],
        )
        for n in range(50)
    ]


def _run(rates: dict[tuple[str, str], str]) -> tuple[dict, FakeProvider]:
    month_end = importlib.import_module("app.billing.month_end")
    provider = FakeProvider(rates)
    totals = month_end.run_month_end(_invoices(), "GBP", FxRatesClient("http://fx.test", http_get=provider))
    return totals, provider


def test_each_currency_pair_requested_once_per_run():
    totals, provider = _run({("EUR", "GBP"): "0.85", ("USD", "GBP"): "0.75"})
    assert totals["INV-0"] == Decimal("114.50")
    assert len(totals) == 50
    assert provider.requests == Counter({("EUR", "GBP"): 1, ("USD", "GBP"): 1})


def test_cached_rates_do_not_outlive_the_run():
    """A module-level or global memo would serve last month's rates to this month's run."""
    _run({("EUR", "GBP"): "0.85", ("USD", "GBP"): "0.75"})
    totals, provider = _run({("EUR", "GBP"): "0.90", ("USD", "GBP"): "0.80"})
    assert totals["INV-0"] == Decimal("121.00")
    assert provider.requests == Counter({("EUR", "GBP"): 1, ("USD", "GBP"): 1})


def test_fx_client_itself_stays_uncached():
    """Caching wraps the client at the run boundary; live quotes through the client still ask the provider."""
    live_quote = importlib.import_module("app.quotes.live_quote")
    provider = FakeProvider({("EUR", "GBP"): "0.85"})
    fx = FxRatesClient("http://fx.test", http_get=provider)
    live_quote.quote_price(Decimal("10"), "EUR", "GBP", fx)
    provider.rates[("EUR", "GBP")] = "0.86"
    assert live_quote.quote_price(Decimal("10"), "EUR", "GBP", fx) == Decimal("8.60")
    assert provider.requests[("EUR", "GBP")] == 2


def _invoice_total_function() -> ast.FunctionDef:
    for path in sorted(BILLING.rglob("*.py")):
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node, ast.FunctionDef) and node.name == "invoice_total_in":
                return node
    pytest.fail("invoice_total_in no longer exists in app/billing (render_invoice_summary depends on it)")


def test_invoice_total_logic_has_no_cache_bookkeeping():
    """The conversion logic stays unaware of caching: no membership checks, memo writes or global state."""
    func = _invoice_total_function()
    offenders = []
    for node in ast.walk(func):
        if isinstance(node, ast.Compare) and any(isinstance(op, (ast.In, ast.NotIn)) for op in node.ops):
            offenders.append(f"line {node.lineno}: membership check")
        elif isinstance(node, (ast.Global, ast.Nonlocal)):
            offenders.append(f"line {node.lineno}: global/nonlocal")
        elif isinstance(node, ast.Assign) and any(isinstance(t, ast.Subscript) for t in node.targets):
            offenders.append(f"line {node.lineno}: memo write")
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "setdefault":
            offenders.append(f"line {node.lineno}: setdefault")
    assert not offenders, offenders
