import re
import subprocess
import sys

import pytest

sys.path.insert(0, "/tests")
import atlas  # noqa: E402
import code_truth  # noqa: E402

TARGET = "loyalty.points.points_for"
# Reached only through `getattr(service, step)`: a real caller the static graph cannot see.
DYNAMIC_ONLY = {"cmd_replay"}
# The Protocol method sits between BackfillJob.run and the implementation; a graph may show it or skip it.
DISPATCH_HOPS = {"Accrual.accrue"}


@pytest.fixture(scope="module")
def page():
    return atlas.page()


@pytest.fixture(scope="module")
def code():
    return code_truth.load("/app")


@pytest.fixture(scope="module")
def ripple(page):
    return atlas.transitive_callers(atlas.graph(page), "points_for")


def test_one_html_page_holds_the_visuals():
    pages = atlas.html_pages()
    assert len(pages) == 1, [str(p) for p in pages]


def test_page_names_the_commit_it_was_drawn_from(page):
    head = subprocess.run(["git", "-C", "/app", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    assert re.search(rf"\b{head[:7]}", page), f"short SHA {head[:7]} of the diagrammed commit not on the page"


def test_page_embeds_the_dependency_graph(page):
    g = atlas.graph(page)
    assert any(atlas.symbol_key(i) == "points_for" for i in atlas.node_ids(g)), atlas.node_ids(g)


def test_graph_symbols_exist_in_the_code(page, code):
    known = code.symbol_keys()
    invented = sorted({atlas.symbol_key(i) for i in atlas.node_ids(atlas.graph(page))} - known)
    assert not invented, f"graph nodes with no definition in the code: {invented}"


def test_ripple_includes_every_real_caller(ripple, code):
    truth = code.transitive_callers(TARGET) - DISPATCH_HOPS
    missing = sorted(truth - ripple)
    assert not missing, f"transitive callers of points_for missing from the graph: {missing}"


def test_ripple_excludes_same_name_method_and_unrelated_code(ripple, code):
    allowed = code.transitive_callers(TARGET) | DYNAMIC_ONLY | DISPATCH_HOPS
    functions = {code.key(q) for q in code.functions}
    extra = sorted((ripple & functions) - allowed)
    assert not extra, f"graph says these call points_for, but they do not: {extra}"


def test_notes_flag_the_getattr_caller_the_graph_misses():
    assert re.search(r"replay", atlas.notes(), re.I), "NOTES.md does not mention the replay command reached via getattr"
