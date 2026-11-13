import pytest

from app.payments import Gateway, GatewayConfig


@pytest.fixture
def gateway_in_test_mode() -> Gateway:
    return Gateway(GatewayConfig(api_key="sk_test_abc", test_mode=True))


@pytest.fixture
def live_gateway() -> Gateway:
    return Gateway(GatewayConfig(api_key="sk_live_abc"))
