from datetime import date

from app.shipping.eta import delivery_eta, latdelivery_eta

FRIDAY = date(2026, 3, 6)


def test_delivery_eta_skips_weekends():
    assert delivery_eta(FRIDAY, "standard") == date(2026, 3, 11)


def test_delivery_eta_express_next_working_day():
    assert delivery_eta(FRIDAY, "express") == date(2026, 3, 9)


def test_latdelivery_eta_adds_buffer():
    assert latdelivery_eta(FRIDAY, "standard") == date(2026, 3, 13)
