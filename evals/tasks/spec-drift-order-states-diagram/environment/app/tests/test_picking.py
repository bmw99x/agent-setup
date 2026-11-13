from app.orders.picking import pick_zone


def test_fast_movers_go_to_zone_a():
    """SKUs picked 20+ times a day live in zone A."""
    assert pick_zone(25) == "A"
