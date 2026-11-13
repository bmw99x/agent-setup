from app.shipping.manifest import build_manifest


def test_manifest_line_has_reference_service_and_address(shipment) -> None:
    assert build_manifest([shipment]) == (
        "ORD-1001;next_day;2;JO BLOGGS / 1 High Street / Flat 2 / York YO1 7HH / GB"
    )
