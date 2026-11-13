import pytest

from app.payments import GatewayConfig
from app.payments.config import GatewayConfigError


def test_test_mode_defaults_off():
    assert GatewayConfig(api_key="sk_live_abc").test_mode is False


def test_mode_skips_capture(gateway_in_test_mode):
    charge = gateway_in_test_mode.charge(1250)
    assert charge.simulated is True
    assert charge.captured is False


def test_mode_rejects_live_key():
    with pytest.raises(GatewayConfigError):
        GatewayConfig(api_key="sk_live_abc", test_mode=True)


def test_mode_flag_exposed_on_gateway(gateway_in_test_mode, live_gateway):
    assert gateway_in_test_mode.test_mode is True
    assert live_gateway.test_mode is False


def test_live_charge_captures(live_gateway):
    charge = live_gateway.charge(1250)
    assert charge.captured is True
    assert charge.simulated is False


def test_charge_rejects_non_positive_amount(live_gateway):
    with pytest.raises(ValueError):
        live_gateway.charge(0)
