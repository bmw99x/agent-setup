from decimal import Decimal

from app.fx import convert

RATES = {"EUR": {"fixing": Decimal("0.85"), "intraday": Decimal("0.86")}}


def test_gbp_passes_through():
    assert convert(1000, "GBP", RATES) == 1000


def test_fixing_used_by_default():
    assert convert(1000, "EUR", RATES) == 850


def test_latest_mode_uses_intraday_rate():
    assert convert(1000, "EUR", RATES, latest_mode=True) == 860
