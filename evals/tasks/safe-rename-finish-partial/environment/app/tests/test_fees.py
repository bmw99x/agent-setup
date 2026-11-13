from app.shipping.fees import delivery_fee


def tdelivery_eta_fee_flat_up_to_2kg():
    assert delivery_fee(2) == 395


def tdelivery_eta_fee_charges_each_started_kg_over_2kg():
    assert delivery_fee(3.2) == 395 + 2 * 120
