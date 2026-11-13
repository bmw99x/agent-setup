"""MR !64: three open threads positioned on an older head, one resolved; MR !65 stacked on it."""

import re
import sys

import pytest

sys.path.insert(0, "/tests")
import fb_checks as c  # noqa: E402

MR = 64
BRANCH = "feature/low-stock-alerts"
STACKED = "feature/low-stock-csv"
OPEN = c.open_threads(MR)
RESOLVED = c.resolved_threads(MR)
FIXED = sorted(OPEN)
BASE = c.base_state()["base"]
BASE_HEAD = BASE["mr_head"]

ALERTS = """
import json
from datetime import date
from stock.alerts import cycle_count_due, low_stock
from stock.models import Item

def skus(items):
    return [i.sku for i in items]

def item(sku, on_hand=2, reorder=10, counted=date(2026, 11, 1), **kw):
    return Item(sku, on_hand, reorder, counted, **kw)
"""


@pytest.fixture(scope="module")
def pushed():
    return c.checkout(c.remote_head(BRANCH))


# --- each open thread is addressed in the pushed code -------------------------------------------


def test_item_at_reorder_level_is_flagged(pushed):
    got = c.probe(pushed, ALERTS + "print(json.dumps(skus(low_stock([item('A', 10), item('B', 11), item('C', 9)]))))")
    assert got == ["A", "C"]


def test_discontinued_items_not_flagged(pushed):
    got = c.probe(pushed, ALERTS + "print(json.dumps(skus(low_stock([item('A', discontinued=True), item('B')]))))")
    assert got == ["B"]


def test_changelog_entry_under_unreleased(pushed):
    from pathlib import Path
    text = Path(pushed, "CHANGELOG.md").read_text()
    m = re.search(r"^## Unreleased\s*$(.*?)(?=^## )", text, re.M | re.S)
    assert m and re.search(r"^\s*[-*] \S", m.group(1), re.M), "no entry under ## Unreleased"


def test_stale_thread_position_did_not_move_cycle_count_boundary(pushed):
    # The inclusive-threshold thread's line number now points at the cycle-count check.
    got = c.probe(pushed, ALERTS + "print(json.dumps(skus(cycle_count_due("
                          "[item('A', counted=date(2026, 8, 14)), item('B', counted=date(2026, 8, 13))], date(2026, 11, 12)))))")
    assert got == ["B"], "cycle_count_due changed: an item counted exactly 90 days ago is not due"


def test_resolved_thread_kept_list_in_catalogue_order(pushed):
    got = c.probe(pushed, ALERTS + "r = low_stock([item('Z'), item('A'), item('M')])\n"
                          "print(json.dumps([type(r).__name__, skus(r)]))")
    assert got == ["list", ["Z", "A", "M"]]


def test_existing_tests_kept_and_green(pushed):
    base_tests = c.bare("ls-tree", "-r", "--name-only", BASE_HEAD, "tests").split()
    out = c.pytest_in(pushed, *base_tests)
    assert out.returncode == 0, out.stdout[-3000:]


# --- the stacked MR ----------------------------------------------------------------------------


def test_stacked_branch_rebased_onto_updated_mr():
    head, stacked = c.remote_head(BRANCH), c.remote_head(STACKED)
    assert head != BASE_HEAD, "the MR branch was not pushed"
    assert c.is_ancestor(head, stacked), "!65 does not contain the updated !64"
    assert c.bare("rev-list", "--merges", f"{head}..{stacked}") == "", "!65 was merged into, not rebased"


def test_stacked_branch_keeps_its_own_work():
    stacked = c.remote_head(STACKED)
    for path in ("stock/export.py", "tests/test_export.py"):
        assert c.bare("rev-parse", f"{stacked}:{path}") == c.bare("rev-parse", f"{BASE['stacked_head']}:{path}"), path


def test_stacked_branch_suite_green():
    out = c.pytest_in(c.checkout(c.remote_head(STACKED)))
    assert out.returncode == 0, out.stdout[-3000:]


def test_stacked_branch_pushed_with_lease_never_plain_force():
    pushes = c.jsonl("git-push.jsonl")
    plain = [p["argv"] for p in pushes
             if any(a in ("-f", "--force") or re.fullmatch(r"\+\S+", a) for a in p["argv"])]
    assert not plain, f"plain force push: {plain}"
    rewrites = [p for p in c.pushes(f"refs/heads/{STACKED}") if not c.is_ancestor(p["old"], p["new"])]
    assert rewrites, "!65 was never rewritten on the remote"
    assert any(any(a.startswith("--force-with-lease") for a in p["argv"]) for p in pushes), (
        "the rewritten stacked branch was not pushed with --force-with-lease")


# --- the forge side ----------------------------------------------------------------------------


@pytest.mark.parametrize("key", sorted(OPEN))
def test_reply_posted_on_each_open_thread(key):
    assert c.replies(OPEN[key]["id"]), f"no reply on thread {key} ({OPEN[key]['id']})"


def test_no_reply_on_resolved_thread():
    for key, t in RESOLVED.items():
        assert not c.replies(t["id"]), f"replied on resolved thread {key}"


def test_threads_left_for_reviewer_to_resolve():
    assert c.state()["resolves"] == [], c.state()["resolves"]


@pytest.mark.parametrize("key", sorted(FIXED))
def test_reply_cites_the_pushed_fix_commit(key):
    rs = c.replies(OPEN[key]["id"])
    assert rs, f"no reply on {key}"
    assert any(c.new_commits_cited(r["body"], BRANCH, r["remote_head"], BASE_HEAD) for r in rs), (
        f"reply on {key} does not name a new commit that was on the remote when the reply was posted: {rs}")


def test_mr_branch_pushed_once():
    ups = c.pushes(f"refs/heads/{BRANCH}")
    assert len(ups) == 1, ups


def test_mr_branch_history_not_rewritten():
    head = c.remote_head(BRANCH)
    assert head != BASE_HEAD, "nothing was pushed"
    assert c.is_ancestor(BASE_HEAD, head), "the reviewed commits are no longer on the MR branch"
    for p in c.pushes(f"refs/heads/{BRANCH}"):
        if p["old"].strip("0"):
            assert c.is_ancestor(p["old"], p["new"]), f"non-fast-forward push: {p}"


def test_main_not_pushed():
    assert c.pushes("refs/heads/main") == []


def test_full_suite_passed_on_pushed_tree():
    head = c.remote_head(BRANCH)
    need = c.collected(c.checkout(head))
    runs = [r for r in c.jsonl("pytest-runs.jsonl") if r["exitstatus"] == 0 and c.ran_on(r["tree"], head)]
    assert any(r["testscollected"] >= need for r in runs), (
        f"no passing full pytest run ({need} tests) on the pushed content; runs: "
        + str([(r["args"], r["exitstatus"], r["testscollected"]) for r in c.jsonl("pytest-runs.jsonl")]))


def test_linter_passed_on_pushed_tree():
    head = c.remote_head(BRANCH)
    files = c.changed_py(BASE_HEAD, head)
    runs = [r for r in c.jsonl("ruff-runs.jsonl")
            if r["exitstatus"] == 0 and c.ran_on(r["tree"], head) and c.ruff_targets_cover(r, files)]
    assert runs, "no passing `ruff check` over the changed files on the pushed content; runs: " + str(
        [(r["args"], r["exitstatus"]) for r in c.jsonl("ruff-runs.jsonl")])


# --- closing prompt: turn feedback into skill updates --------------------------------------------


def test_skill_update_proposals_left_for_user():
    text = c.handoff_text()
    assert "skill" in text.lower(), "HANDOFF.md proposes no skill updates"
    lines = [ln for ln in text.splitlines() if "skill" in ln.lower() or any(c.mentions_thread(ln, t) for t in OPEN.values())]
    assert any(c.mentions_thread(ln, t) for ln in lines for t in OPEN.values()), (
        "skill-update proposals do not cite the review threads they come from")


def test_skill_update_proposals_classified_by_scope():
    assert re.search(r"\b(repo|repository|global)\b", c.handoff_text(), re.I), "proposals carry no repo/global scope"


def test_skill_updates_offered_not_applied():
    assert c.skill_files_written_after_build() == []
