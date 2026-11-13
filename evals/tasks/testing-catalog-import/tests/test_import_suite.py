import pytest
from conftest import run_pytest, unused_production_defs, workspace

IMPORTER = "app/catalog/importer.py"
REPOSITORY = "app/catalog/repository.py"
DEDUPE_THEN_FETCH = """            if self._repository.get(sku) is not None:
                report.duplicates.append(sku)
                continue
            try:
                image = self._images.fetch(row["image_url"])
"""
FETCH_THEN_DEDUPE = """            try:
                image = self._images.fetch(row["image_url"])
            except ImageUnavailableError as error:
                report.failed[sku] = str(error)
                continue
            if self._repository.get(sku) is not None:
                report.duplicates.append(sku)
                continue
            try:
                pass
"""
MUTANTS = {
    "sku_not_normalised": {IMPORTER: [("return raw.strip().upper()", "return raw.strip()")]},
    "duplicate_image_downloaded": {IMPORTER: [(DEDUPE_THEN_FETCH, FETCH_THEN_DEDUPE)]},
    "repository_lookup_misses": {REPOSITORY: [("return None if row is None else Product(*row)", "return None")]},
    "repository_add_not_stored": {REPOSITORY: [(
        '"INSERT INTO products (sku, name, price_pence, image_key) VALUES (?, ?, ?, ?)",', '"SELECT ?, ?, ?, ?",')]},
}


def test_suite_passes_on_unmodified_production_code(agent_files):
    proc = run_pytest(workspace())
    assert proc.returncode == 0, proc.stdout[-3000:]


@pytest.mark.parametrize("mutant", sorted(MUTANTS))
def test_suite_detects_behaviour_change(agent_files, mutant):
    """Only the slow image download is faked; duplicate detection runs through the real repository."""
    proc = run_pytest(workspace(MUTANTS[mutant]))
    assert proc.returncode == 1, f"suite still passes with mutant {mutant}:\n{proc.stdout[-2000:]}"


def test_no_test_only_methods_added_to_production():
    offenders = unused_production_defs()
    assert not offenders, "production defs nothing in app/ calls:\n" + "\n".join(offenders)
