from datetime import date

from app.shipping.eta import est_delivery, latest_delivery

FRIDAY = date(2026, 3, 6)


def test_est_delivery_skips_weekends():
    assert est_delivery(FRIDAY, "standard") == date(2026, 3, 11)


def test_est_delivery_express_next_working_day():
    assert est_delivery(FRIDAY, "express") == date(2026, 3, 9)


def test_latest_delivery_adds_buffer():
    assert latest_delivery(FRIDAY, "standard") == date(2026, 3, 13)
