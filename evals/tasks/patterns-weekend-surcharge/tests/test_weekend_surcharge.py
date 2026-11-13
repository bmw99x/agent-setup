import ast
import re
import subprocess
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, "/app")

from app.delivery.checkout import order_total  # noqa: E402
from app.delivery.fees import delivery_fee  # noqa: E402
from app.delivery.models import Order  # noqa: E402

PACKAGE = Path("/app/app")
FEES = PACKAGE / "delivery" / "fees.py"
BASELINE_MODULES = {
    "__init__.py",
    "delivery/__init__.py",
    "delivery/models.py",
    "delivery/fees.py",
    "delivery/checkout.py",
}
BASELINE_CLASSES = {"Order"}
BASELINE_FEE_FUNCTIONS = {"delivery_fee"}
MAX_NEW_HELPERS = 2

WEDNESDAY = date(2026, 3, 4)
FRIDAY = date(2026, 3, 6)
SATURDAY = date(2026, 3, 7)
SUNDAY = date(2026, 3, 8)
MONDAY = date(2026, 3, 9)


def _modules() -> list[Path]:
    return sorted(PACKAGE.rglob("*.py"))


def _trees() -> list[ast.Module]:
    return [ast.parse(path.read_text()) for path in _modules()]


def _order(subtotal: str, km: int, day: date) -> Order:
    return Order("o", Decimal(subtotal), km, day)


def test_weekend_deliveries_cost_two_pounds_more():
    assert delivery_fee(_order("20", 3, SATURDAY)) == Decimal("5.50")
    assert delivery_fee(_order("20", 10, SUNDAY)) == Decimal("7.50")


def test_weekday_fees_unchanged():
    for day in (MONDAY, WEDNESDAY, FRIDAY):
        assert delivery_fee(_order("20", 3, day)) == Decimal("3.50")
        assert delivery_fee(_order("20", 10, day)) == Decimal("5.50")


def test_free_delivery_stays_free_at_weekends():
    assert delivery_fee(_order("50", 3, SATURDAY)) == Decimal("0")
    assert delivery_fee(_order("80", 12, SUNDAY)) == Decimal("0")


def test_checkout_total_includes_surcharge():
    assert order_total(_order("20", 3, SATURDAY)) == Decimal("25.50")


def test_project_tests_pass():
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "/app/tests", "-q", "-p", "no:cacheprovider"],
        cwd="/app", capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stdout[-2000:]


def test_no_new_module_for_one_surcharge():
    added = {str(p.relative_to(PACKAGE)) for p in _modules()} - BASELINE_MODULES
    assert not added, f"new modules for a single surcharge: {sorted(added)}"


def test_no_new_class_for_one_surcharge():
    classes = {n.name for tree in _trees() for n in ast.walk(tree) if isinstance(n, ast.ClassDef)}
    added = classes - BASELINE_CLASSES
    assert not added, f"new classes for a single surcharge: {sorted(added)}"


def test_no_abstract_interface_or_protocol():
    for path in _modules():
        text = path.read_text()
        for token in ("ABC", "ABCMeta", "abstractmethod", "Protocol"):
            assert not re.search(rf"\b{token}\b", text), f"{path}: {token} introduced"


def test_no_rule_registry_for_one_surcharge():
    tree = ast.parse(FEES.read_text())
    functions = {n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    for node in tree.body:
        if isinstance(node, (ast.Assign, ast.AnnAssign)) and node.value is not None:
            if isinstance(node.value, (ast.List, ast.Tuple, ast.Dict, ast.Set)):
                referenced = {n.id for n in ast.walk(node.value) if isinstance(n, ast.Name)}
                assert not referenced & functions, "collection of surcharge functions for a single rule"


def test_at_most_a_small_helper_added():
    tree = ast.parse(FEES.read_text())
    functions = {n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    added = functions - BASELINE_FEE_FUNCTIONS
    assert len(added) <= MAX_NEW_HELPERS, f"too many new functions for one surcharge: {sorted(added)}"
