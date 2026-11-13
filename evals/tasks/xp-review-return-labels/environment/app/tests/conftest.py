import pytest

from app.shipping.models import Address, Parcel, Shipment


@pytest.fixture
def shipment() -> Shipment:
    return Shipment(
        reference="ORD-1001",
        sender=Address("Acme Warehouse", "Unit 4 Dock Road", "Leeds", "LS1 4AB", "gb"),
        recipient=Address("Jo Bloggs", "1 High Street", "York", "YO1 7HH", "gb", line2="Flat 2"),
        service="next_day",
        parcels=(Parcel(1200, "boots"), Parcel(350, "socks")),
    )
