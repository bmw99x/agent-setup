import ast
import dataclasses
import importlib
import inspect
import sys
from decimal import Decimal
from pathlib import Path
from typing import is_typeddict

import pytest
from pydantic import BaseModel

sys.path.insert(0, "/app")

PACKAGE = Path("/app/app/shipping")
WIRE_KEYS = ("carrierCode", "serviceName", "totalPence", "currencyCode", "etaDays", "weightKg", "postalCode")

RATES = {
    "rates": [
        {"carrierCode": "RM", "serviceName": "Tracked 48", "totalPence": 395, "currencyCode": "GBP", "etaDays": 2},
        {"carrierCode": "DPD", "serviceName": "Next Day", "totalPence": 899, "currencyCode": "GBP", "etaDays": 1},
    ]
}


class FakeParcelHub:
    def __init__(self, response):
        self.response = response
        self.payloads = []

    def get_rates(self, payload):
        if hasattr(payload, "model_dump"):
            payload = payload.model_dump(by_alias=True)
        self.payloads.append(payload)
        return self.response


def _service(response):
    from app.shipping.models import Parcel
    from app.shipping.service import ShippingService

    client = FakeParcelHub(response)
    return ShippingService(client), client, Parcel(weight_grams=1250, postcode="SW1A 1AA")


def _is_dto(cls):
    return (isinstance(cls, type) and issubclass(cls, BaseModel)) or dataclasses.is_dataclass(cls) or is_typeddict(cls)


def _local_dtos(module):
    return [c for _, c in inspect.getmembers(module) if inspect.isclass(c) and c.__module__ == module.__name__ and _is_dto(c)]


def test_quotes_for_maps_rates_to_domain_quotes():
    service, client, parcel = _service(RATES)
    quotes = service.quotes_for(parcel)
    assert [(q.carrier, q.service, q.price, q.currency, q.delivery_days) for q in quotes] == [
        ("RM", "Tracked 48", Decimal("3.95"), "GBP", 2),
        ("DPD", "Next Day", Decimal("8.99"), "GBP", 1),
    ]
    sent = client.payloads[0]
    assert float(sent["weightKg"]) == pytest.approx(1.25)
    assert sent["destination"]["postalCode"] == "SW1A 1AA"


def test_malformed_rate_response_fails_at_boundary():
    service, _, parcel = _service({"rates": [{"carrierCode": "RM", "serviceName": "Tracked 48", "currencyCode": "GBP", "etaDays": 2}]})
    with pytest.raises(Exception):
        service.quotes_for(parcel)


def test_rate_response_model_lives_in_package_dtos_module():
    module = importlib.import_module("app.shipping.dtos")
    assert _local_dtos(module), "app/shipping/dtos.py defines no pydantic model / dataclass / TypedDict"


def test_parcelhub_translation_lives_in_package_adapters_module():
    importlib.import_module("app.shipping.adapters")
    service_tree = ast.parse((PACKAGE / "service.py").read_text())
    imported = {
        node.module
        for node in ast.walk(service_tree)
        if isinstance(node, ast.ImportFrom) and node.module
    } | {
        f".{node.module or ''}" for node in ast.walk(service_tree) if isinstance(node, ast.ImportFrom) and node.level
    }
    assert imported & {"app.shipping.adapters", ".adapters"}, "service.py does not use app.shipping.adapters"


def test_service_holds_no_wire_format_mapping():
    text = (PACKAGE / "service.py").read_text()
    leaked = [key for key in WIRE_KEYS if key in text]
    assert not leaked, f"ParcelHub wire keys in service.py: {leaked}"


def test_service_defines_no_dto_classes():
    module = importlib.import_module("app.shipping.service")
    assert not _local_dtos(module), "DTO classes defined in service.py"
