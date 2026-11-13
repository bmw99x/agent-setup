from datetime import UTC, date, datetime

import pytest

from app.db import connect
from app.shipments.service import ShipmentNotFoundError, ShipmentService

NOW = datetime(2026, 3, 2, 9, 30, tzinfo=UTC)


@pytest.fixture
def service():
    return ShipmentService(connect(), clock=lambda: NOW)


def test_schedule_records_event(service):
    shipment = service.schedule("ORD-1", "sw1a 1aa", date(2026, 3, 5))
    assert shipment.status == "scheduled"
    assert shipment.postcode == "SW1A 1AA"
    assert [event.kind for event in service.history(shipment.id)] == ["scheduled"]


def test_dispatch(service):
    shipment = service.schedule("ORD-1", "SW1A 1AA", date(2026, 3, 5))
    assert service.dispatch(shipment.id).status == "dispatched"
    assert service.count_by_status() == {"dispatched": 1}


def test_unknown_shipment(service):
    with pytest.raises(ShipmentNotFoundError):
        service.get(999)
