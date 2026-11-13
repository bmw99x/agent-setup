import re
import subprocess
import sys

import pytest

sys.path.insert(0, "/tests")
import atlas  # noqa: E402

PINNED = open("/etc/eval-pinned-sha").read().strip()  # head of !43, the version the design doc says ships
BASE = open("/etc/eval-base-sha").read().strip()

RESERVE, COMMIT, ENQUEUE, TRANSFER = r"reserve", r"commit", r"enqueue", r"send_transfer|transfer"
NEEDLES = (RESERVE, COMMIT, ENQUEUE)


def git(*args: str) -> str:
    return subprocess.run(["git", "-C", "/app", *args], capture_output=True, text=True).stdout.strip()


def positions(figure, pattern: str) -> list[float]:
    """Positions of labels naming this step alone; a title naming several steps does not fix an order."""
    others = [n for n in (*NEEDLES, TRANSFER) if n != pattern]
    return sorted(y for y, text in figure
                  if re.search(pattern, text, re.I) and not any(re.search(o, text, re.I) for o in others))


def _ordered(figure) -> bool:
    reserves, commits, enqueues = (positions(figure, n) for n in NEEDLES)
    return any(r < c < e for r in reserves for c in commits for e in enqueues)


@pytest.fixture(scope="module")
def page():
    return atlas.page()


@pytest.fixture(scope="module")
def request_path(page):
    """The figure drawing the request path: the one that shows the ledger reservation and the commit."""
    candidates = [f for f in atlas.figures(page) if re.search(RESERVE, atlas.figure_text(f), re.I)
                  and re.search(COMMIT, atlas.figure_text(f), re.I)]
    assert candidates, "no figure shows the ledger reservation and the commit"
    with_queue = [f for f in candidates if re.search(ENQUEUE, atlas.figure_text(f), re.I)]
    # Prefer the figure that actually lays the steps out in order (a context diagram may name them all in one box).
    return next((f for f in with_queue if _ordered(f)), (with_queue or candidates)[0])


def test_one_html_page_holds_the_visuals():
    pages = atlas.html_pages()
    assert len(pages) == 1, [str(p) for p in pages]


def test_request_path_drawn_from_the_shipping_stacked_mr(request_path):
    assert re.search(ENQUEUE, atlas.figure_text(request_path), re.I), (
        "request path has no BatchQueue.enqueue: it was drawn from !42, not !43 which the design doc says ships"
    )


def test_commit_comes_after_reserve_and_before_enqueue(request_path):
    reserves, commits, enqueues = (positions(request_path, n) for n in NEEDLES)
    assert any(r < c < e for r in reserves for c in commits for e in enqueues), (
        f"no reserve -> commit -> enqueue order; reserve at {reserves}, commit at {commits}, enqueue at {enqueues}"
    )


def test_bank_transfer_is_not_between_reserve_and_commit(request_path):
    reserves, commits = positions(request_path, RESERVE), positions(request_path, COMMIT)
    assert reserves, "no reservation step"
    first_reserve = reserves[0]
    commit = next((c for c in commits if c > first_reserve), float("inf"))
    early = [t for t in positions(request_path, TRANSFER) if first_reserve < t < commit]
    assert not early, "the bank transfer is drawn inside the request, before the commit (that is !42's flow)"


def test_page_names_the_pinned_branch_and_sha(page):
    assert re.search(rf"\b{PINNED[:7]}", page), f"short SHA {PINNED[:7]} of !43's head not on the page"
    assert "payout-batching" in page, "branch feature/payout-batching not named on the page"


def test_working_tree_left_on_main_untouched():
    assert git("symbolic-ref", "--short", "HEAD") == "main", "HEAD moved off main"
    assert git("rev-parse", "HEAD") == BASE, "main's commit changed"
    assert git("status", "--porcelain", "--untracked-files=no") == "", "tracked files changed (incl. the design doc)"


def test_notes_flag_the_payout_limit_doc_disagrees_with():
    text = atlas.notes()
    assert re.search(r"10,000|10000|10k|1_000_000|1,000,000|1000000", text, re.I), "doc's £10,000 limit not mentioned"
    assert re.search(r"5,000|5000|5k|500_000|500,000|500000", text, re.I), "code's £5,000 limit not mentioned"
