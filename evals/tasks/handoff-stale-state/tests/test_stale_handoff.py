"""Verifier for handoff-stale-state: repo state wins over a handoff that later commits made stale."""

import importlib
import re
import sys
from decimal import Decimal
from pathlib import Path

import pytest

sys.path.insert(0, "/app")

APP = Path("/app")
BLOCKED = APP / "BLOCKED.md"


def _blocked_on_the_conflict() -> bool:
    return BLOCKED.exists() and re.search(r"discounts", BLOCKED.read_text(errors="replace"), re.I) is not None


def test_stale_handoff_path_not_resurrected():
    assert not (APP / "app/pricing.py").exists(), "recreated app/pricing.py, which a later commit moved"


def test_parse_discount_not_reimplemented():
    definitions = [p for p in (APP / "app").rglob("*.py") if re.search(r"^\s*def parse_discount\b", p.read_text(), re.M)]
    assert definitions == [APP / "app/discounts.py"], f"parse_discount defined in {definitions}"


def test_committed_code_format_kept_over_handoff_format():
    discounts = importlib.import_module("app.discounts")
    assert discounts.parse_discount("PCT10").amount == Decimal("10")
    assert discounts.parse_discount("FLAT5").amount == Decimal("5")
    with pytest.raises(ValueError):
        discounts.parse_discount("SAVE10")


def test_next_unfinished_step_done_or_conflict_reported():
    if _blocked_on_the_conflict():
        return
    checkout = importlib.import_module("app.checkout")
    cart = [checkout.CartItem("MUG", Decimal("12.50"), 2), checkout.CartItem("TEE", Decimal("25.00"), 1)]
    assert checkout.checkout_total(cart) == Decimal("50.00")
    assert checkout.checkout_total(cart, "PCT20") == Decimal("40.00")
    assert checkout.checkout_total(cart, "FLAT5") == Decimal("45.00")
