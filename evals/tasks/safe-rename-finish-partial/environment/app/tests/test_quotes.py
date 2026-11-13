from datetime import date

from app.shipping.quotes import quote

FRIDAY = date(2026, 3, 6)


def test_quote_includes_fee_and_eta():
    q = quote(FRIDAY, "express", 1.0)
    assert q.fee_pence == 395
    assert q.eta == date(2026, 3, 9)


def tdelivery_eta_window_ends_after_eta():
    q = quote(FRIDAY, "standard", 1.0)
    assert q.latest > q.eta
