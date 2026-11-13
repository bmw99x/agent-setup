"""ben-pair: before declaring done, take the refactor beat — the third copy of the revenue loop is
folded into one shared rule, with weekly/monthly behaviour preserved."""
import ast
import subprocess
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, "/app")

from app.orders import Order  # noqa: E402

APP = Path("/app")
APP_PKG = APP / "app"

ORDERS = [
    Order("B1", date(2026, 12, 28), "paid", Decimal("40.00")),
    Order("B2", date(2026, 12, 31), "shipped", Decimal("25.50"), refunded=Decimal("5.50")),
    Order("B3", date(2026, 12, 31), "pending", Decimal("70.00")),
    Order("B4", date(2027, 1, 1), "paid", Decimal("12.345")),
    Order("B5", date(2027, 1, 1), "cancelled", Decimal("300.00")),
    Order("B6", date(2027, 1, 4), "shipped", Decimal("9.99"), refunded=Decimal("9.99")),
]


def _app_trees():
    return [ast.parse(p.read_text()) for p in APP_PKG.rglob("*.py")]


def _attribute_uses(attr: str) -> int:
    return sum(
        1 for tree in _app_trees() for node in ast.walk(tree) if isinstance(node, ast.Attribute) and node.attr == attr
    )


def test_daily_revenue_applies_the_same_rules():
    from app.revenue import daily_revenue

    assert daily_revenue(ORDERS) == {
        "2026-12-28": Decimal("40.00"),
        "2026-12-31": Decimal("20.00"),
        "2027-01-01": Decimal("12.34"),
        "2027-01-04": Decimal("0.00"),
    }


def test_weekly_and_monthly_behaviour_preserved():
    from app.revenue import monthly_revenue, weekly_revenue

    assert monthly_revenue(ORDERS) == {
        "2026-12": Decimal("60.00"),
        "2027-01": Decimal("12.34"),
    }
    assert weekly_revenue(ORDERS) == {
        "2026-W53": Decimal("72.34"),
        "2027-W01": Decimal("0.00"),
    }


def test_earning_status_rule_written_once():
    assert _attribute_uses("status") <= 1, "order-status filter repeated per report"


def test_refund_netting_written_once():
    assert _attribute_uses("refunded") <= 1, "refund netting repeated per report"


def test_rounding_written_once():
    assert _attribute_uses("quantize") <= 1, "rounding repeated per report"


def test_daily_revenue_has_tests_and_suite_passes():
    test_sources = "\n".join(p.read_text() for p in (APP / "tests").rglob("test_*.py"))
    assert "daily_revenue" in test_sources, "no test exercises daily_revenue"
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", str(APP / "tests")],
        cwd=APP,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout[-2000:]
