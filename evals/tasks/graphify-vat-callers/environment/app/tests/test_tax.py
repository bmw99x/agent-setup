import pytest

from app.billing.tax import UnknownCountry, compute_vat


def test_vat_rounds_half_up():
    assert compute_vat(1_003, "DE") == 191


def test_unknown_country_rejected():
    with pytest.raises(UnknownCountry):
        compute_vat(100, "XX")
