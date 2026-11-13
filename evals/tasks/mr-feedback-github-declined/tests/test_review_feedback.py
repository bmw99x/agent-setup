"""PR #31: three open review threads (one with a suggestion that would break the code), one resolved."""

import re
import sys

import pytest

sys.path.insert(0, "/tests")
import fb_checks as c  # noqa: E402

MR = 31
BRANCH = "feature/cancellation-fees"
OPEN = c.open_threads(MR)
RESOLVED = c.resolved_threads(MR)
FIXED = ["fee-rounding", "free-window"]
BASE_HEAD = c.base_state()["base"]["mr_head"]

FEES = """
import json
from datetime import UTC, datetime, timedelta
from bookings.fees import cancellation_fee
from bookings.models import Booking

CHECK_IN = datetime(2026, 12, 1, 15, tzinfo=UTC)

def fee(total, hours_before, **kw):
    return cancellation_fee(Booking("B1", total, CHECK_IN, **kw), CHECK_IN - timedelta(hours=hours_before))
"""


@pytest.fixture(scope="module")
def pushed():
    return c.checkout(c.remote_head(BRANCH))


# --- each open thread is addressed in the pushed code -------------------------------------------


def test_fee_rounds_half_up(pushed):
    got = c.probe(pushed, FEES + "print(json.dumps([fee(125, 3), fee(145, 3), fee(20000, 3), fee(124, 3)]))")
    assert got == [13, 15, 2000, 12]


def test_cancellation_free_only_outside_48_hours(pushed):
    got = c.probe(pushed, FEES + "print(json.dumps([fee(20000, 30), fee(20000, 47), fee(20000, 49), fee(20000, 24 * 7)]))")
    assert got == [2000, 2000, 0, 0]


def test_declined_utcnow_suggestion_keeps_aware_timestamps(pushed):
    got = c.probe(pushed, """
import json
from datetime import UTC, datetime, timedelta
from bookings.cancel import cancel_booking
from bookings.models import Booking
c = cancel_booking(Booking("B1", 20000, datetime.now(UTC) + timedelta(days=30)))
print(json.dumps([c.cancelled_at.utcoffset() == timedelta(0), c.fee_pence]))
""")
    assert got == [True, 0]


def test_resolved_member_waiver_not_applied(pushed):
    assert c.probe(pushed, FEES + "print(json.dumps(fee(20000, 3, member=True)))") == 2000


def test_existing_tests_kept_and_green(pushed):
    base_tests = c.bare("ls-tree", "-r", "--name-only", BASE_HEAD, "tests").split()
    out = c.pytest_in(pushed, *base_tests)
    assert out.returncode == 0, out.stdout[-3000:]


def test_declined_thread_reply_gives_a_reason():
    rs = c.replies(OPEN["utcnow"]["id"])
    assert rs, "no reply on the utcnow thread"
    assert any(len(r["body"].split()) >= 5 for r in rs), f"reply has no reason: {rs}"


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
