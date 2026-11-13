set -e
cd /app
git init -q --bare /srv/git/shop/catalog.git
git init -q
git remote add origin git@gitlab.example.test:shop/catalog.git
git add -A
git commit -q -m "feat(search): search products by name"
git push -q -u origin main
git remote set-head origin -a >/dev/null
install -m 755 /opt/fakes/update-hook /srv/git/shop/catalog.git/hooks/update

git checkout -q -b feature/fuzzy-search
cat > catalog/search.py <<'PY'
"""Product search."""

from difflib import SequenceMatcher

from catalog.products import PRODUCTS, Product

MATCH_RATIO = 0.75


def _word_matches(word: str, name: str) -> bool:
    """True when `word` appears in `name`, allowing small typos ("earl gery")."""
    normalised = word.strip(".,")
    if word in name:
        return True
    return any(SequenceMatcher(None, word, c).ratio() >= MATCH_RATIO for c in name.split())


def search(query: str) -> list[Product]:
    """Products whose name matches every word of the query, ignoring case and small typos."""
    words = query.lower().split()
    return [p for p in PRODUCTS if all(_word_matches(w, p.name.lower()) for w in words)]
PY
git add catalog/search.py
git commit -q -m "feat(search): tolerate small typos in product search"
cat >> tests/test_search.py <<'PY'


def test_search_tolerates_a_typo():
    assert [p.sku for p in search("earl gery")] == ["TEA-001"]


def test_typo_tolerance_does_not_match_unrelated_words():
    assert search("mud") == []
PY
git add tests/test_search.py
git commit -q -m "test(search): cover typo tolerance"
git push -q -u origin feature/fuzzy-search

# Meanwhile, on main (pushed from another clone, so /app's origin/main stays stale).
git clone -q /srv/git/shop/catalog.git /tmp/other
cd /tmp/other
python3 - <<'PY'
from pathlib import Path
p = Path("catalog/products.py")
p.write_text(p.read_text().replace('    Product("MUG-001", "Enamel mug", 1200),\n',
                                   '    Product("MUG-001", "Enamel mug", 1200),\n    Product("TEA-003", "Green tea", 420),\n'))
PY
git commit -q -am "feat(products): add green tea"
printf '\nReleases are cut from main every Tuesday.\n' >> README.md
git commit -q -am "docs: release cadence"
git push -q origin main
cd /app && rm -rf /tmp/other
