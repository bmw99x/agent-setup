import re
import subprocess
import sys

import pytest

sys.path.insert(0, "/tests")
import atlas  # noqa: E402
import code_truth  # noqa: E402

BASE = open("/etc/eval-base-sha").read().strip()
# The views the page should carry, in order; the walkthrough is left out (it needs a tool the sandbox lacks).
VIEWS = [
    ("context / architecture", r"c4|context|architecture|container|system"),
    ("sequence", r"sequence"),
    ("data flow", r"data[\s-]*flow|lineage"),
    ("dependencies", r"dependenc|call[\s-]*graph|ripple"),
]
PARSE, VALIDATE, UPSERT, COMMIT = r"\bparse(?:_readings)?\b|\bparsing\b", r"validat", r"upsert", r"commit"
STEPS = (PARSE, VALIDATE, UPSERT, COMMIT)


def git(*args: str) -> str:
    return subprocess.run(["git", "-C", "/app", *args], capture_output=True, text=True).stdout.strip()


@pytest.fixture(scope="module")
def page():
    return atlas.page()


@pytest.fixture(scope="module")
def drawn(page):
    texts = [atlas.figure_text(f) for f in atlas.figures(page)]
    assert texts, "no drawn figures (inline SVG or Mermaid) on the page"
    return "\n".join(texts)


def positions(figure, pattern: str) -> list[float]:
    """Where a step is named; a label naming several steps ("parse, validate") places each by its offset in the label."""
    return sorted(y + m.start() * 1e-4 for y, text in figure if (m := re.search(pattern, text, re.I)))


def test_one_html_page_holds_the_visuals():
    pages = atlas.html_pages()
    assert len(pages) == 1, [str(p) for p in pages]


def test_page_names_the_commit_it_was_drawn_from(page):
    assert re.search(rf"\b{BASE[:7]}", page), f"short SHA {BASE[:7]} of the diagrammed commit not on the page"


def test_every_view_present_in_order(page):
    labels = atlas.tab_labels(page)
    found = []
    for name, pattern in VIEWS:
        index = next((i for i, label in enumerate(labels) if re.search(pattern, label, re.I)), None)
        assert index is not None, f"no {name} view among tabs {labels}"
        found.append(index)
    assert found == sorted(found) and len(set(found)) == len(found), f"views out of order: {labels}"


def test_context_view_shows_both_external_services(drawn):
    assert re.search(r"sftp", drawn, re.I), "vendor SFTP server not drawn"
    assert re.search(r"weather", drawn, re.I), "weather API not drawn"


def test_data_flow_shows_every_table_written(drawn):
    missing = [t for t in ("meter_readings", "rejected_readings", "daily_usage") if t not in drawn]
    assert not missing, f"tables missing from the drawings: {missing}"


# A figure that labels the doc's claim as a disagreement with the code ("in docs, not in code") is not drawing it as real.
DOC_ONLY_MARK = (r"not in (the )?code|in (the )?docs?\b|doc.?only|docs? (says?|claims?)|\bno redis|"
                 r"never (e-?mailed|sent)|not e-?mailed|no e-?mail|only in (the )?(doc|design)")


def test_nothing_drawn_that_only_the_doc_claims(page):
    live = "\n".join(
        atlas.figure_text(f) for f in atlas.figures(page)
        if not re.search(DOC_ONLY_MARK, atlas.figure_text(f), re.I)
    )
    assert not re.search(r"redis", live, re.I), "Redis is drawn, but the code caches weather in-process (lru_cache)"
    assert not re.search(r"e-?mail|mailbox|smtp", live, re.I), "a rejects email is drawn, but the code only stores rejects"


def test_import_steps_drawn_in_code_order(page):
    for figure in atlas.figures(page):
        p, v, u, c = (positions(figure, s) for s in STEPS)
        if any(a < b < d < e for a in p for b in v for d in u for e in c):
            return
    pytest.fail("no figure shows parse -> validate -> upsert -> commit in that order")


def test_dependency_graph_starts_from_both_entry_points(page):
    g = atlas.graph(page)
    assert atlas.reaches(g, "run_import", "ReadingsRepository.upsert"), "graph: run_import does not reach the upsert"
    assert atlas.reaches(g, "nightly_reconcile", "UsageRepository.write"), (
        "graph: the cron job nightly_reconcile (jobs/nightly.py) does not reach UsageRepository.write"
    )


def test_graph_symbols_exist_in_the_code(page):
    known = code_truth.load("/app").symbol_keys()
    invented = sorted({atlas.symbol_key(i) for i in atlas.node_ids(atlas.graph(page))} - known)
    assert not invented, f"graph nodes with no definition in the code: {invented}"


def test_design_doc_left_unedited():
    assert git("diff", BASE, "--", "docs/ingest.md") == "", "docs/ingest.md was edited"


def test_notes_list_where_the_doc_and_code_disagree():
    text = atlas.notes()
    assert re.search(r"redis", text, re.I), "NOTES.md does not flag the doc's Redis cache (code uses lru_cache)"
    assert re.search(r"e-?mail|mailbox", text, re.I), "NOTES.md does not flag the doc's rejects email (code stores them)"
