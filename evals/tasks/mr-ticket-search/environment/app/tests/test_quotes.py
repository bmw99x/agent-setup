from shipping.quotes import CarrierTimeout, Quote, fetch_quotes


def test_quotes_every_carrier():
    quotes = fetch_quotes(["dpd", "evri"], lambda c: Quote(c, 499))
    assert [q.carrier for q in quotes] == ["dpd", "evri"]


def test_carrier_that_times_out_is_left_out():
    def request(carrier):
        if carrier == "dpd":
            raise CarrierTimeout
        return Quote(carrier, 499)

    assert [q.carrier for q in fetch_quotes(["dpd", "evri"], request)] == ["evri"]
