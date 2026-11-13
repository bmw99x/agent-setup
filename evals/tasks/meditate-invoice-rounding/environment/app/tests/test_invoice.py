import json
from decimal import Decimal
from pathlib import Path

from billing.invoice import InvoiceLine, invoice_total

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


def test_eur_gbp_split():
    fixture = _load("invoice_eur_gbp.json")
    lines = [InvoiceLine(l["description"], Decimal(l["amount"]), Decimal(l["fx_rate"])) for l in fixture["lines"]]
    assert invoice_total(lines) == Decimal(fixture["total"])


def test_single_line_rounds_half_up():
    assert invoice_total([InvoiceLine("x", Decimal("0.125"), Decimal("1"))]) == Decimal("0.13")
