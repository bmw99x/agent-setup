from app.shipping.labels import render_label


def test_render_label_prints_recipient_address_block(shipment) -> None:
    label = render_label(shipment)

    assert "JO BLOGGS\n1 High Street\nFlat 2\nYork YO1 7HH\nGB" in label


def test_render_label_header_shows_service_and_total_weight(shipment) -> None:
    assert "NEXT_DAY | 1.55 kg" in render_label(shipment)


def test_render_label_routes_mainland_next_day(shipment) -> None:
    assert "GB-ND\n" in render_label(shipment)
