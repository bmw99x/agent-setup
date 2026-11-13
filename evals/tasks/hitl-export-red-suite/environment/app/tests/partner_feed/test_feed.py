from app.partner_feed.feed import build_feed


def test_feed_item_carries_price_in_pence():
    products = [{"sku": "MUG-01", "name": "Mug", "price_pence": 1250}]

    assert build_feed(products) == [{"sku": "MUG-01", "title": "Mug", "price_pence": 1250, "currency": "GBP"}]
