from catalog.search import search


def test_search_matches_every_word():
    assert [p.sku for p in search("tea grey")] == ["TEA-001"]


def test_search_ignores_case():
    assert [p.sku for p in search("COFFEE")] == ["COF-001"]
