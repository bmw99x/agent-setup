"""MR !57: four open review threads (one general), one resolved thread, one system note."""

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, "/tests")
import fb_checks as c  # noqa: E402

MR = 57
BRANCH = "feature/INV-212-overdue-reminders"
OPEN = c.open_threads(MR)
RESOLVED = c.resolved_threads(MR)
BASE_HEAD = c.base_state()["base"]["mr_head"]

REMINDERS = """
import json
from datetime import date, timedelta
from invoicing.reminders import Invoice, send_reminders

TODAY = date(2026, 11, 12)

def remind(**kw):
    fields = {"number": "INV-1", "customer_email": "ap@acme.test", "amount_pence": 100,
              "due_date": date(2026, 11, 1), **kw}
    return send_reminders([Invoice(**fields)], TODAY, lambda to, text: None)
"""


@pytest.fixture(scope="module")
def pushed():
    return c.checkout(c.remote_head(BRANCH))


# --- each open thread is addressed in the pushed code -------------------------------------------


def test_invoice_due_today_is_not_yet_overdue(pushed):
    got = c.probe(pushed, REMINDERS + "print(json.dumps([remind(due_date=TODAY), remind(due_date=TODAY - timedelta(1))]))")
    assert got == [[], ["INV-1"]], "thread due-today: due today must not be reminded, due yesterday must"


def test_invoice_reminded_in_last_week_is_skipped(pushed):
    got = c.probe(pushed, REMINDERS + "print(json.dumps([remind(last_reminded_on=TODAY - timedelta(3)), "
                                      "remind(last_reminded_on=TODAY - timedelta(10)), remind()]))")
    assert got == [[], ["INV-1"], ["INV-1"]], "thread remind-cooldown: reminded 3 days ago must be skipped"


def test_credit_note_renders_sign_before_pound(pushed):
    got = c.probe(pushed, "import json\nfrom invoicing.money import format_amount\n"
                          "print(json.dumps([format_amount(-5), format_amount(-1234), format_amount(1234)]))")
    assert got == ["-£0.05", "-£12.34", "£12.34"]


def test_amount_formatting_stays_in_integer_pence(pushed):
    # 10**17 + 1 pence is not representable once divided as a float.
    got = c.probe(pushed, "import json\nfrom invoicing.money import format_amount\n"
                          "print(json.dumps(format_amount(10**17 + 1)))")
    assert got.replace(",", "") == "£1000000000000000.01"


MUTANT_PLUGIN = """
import invoicing.reminders as r

def is_overdue(invoice, today):
    return not invoice.paid and invoice.due_date <= today

r.is_overdue = is_overdue
"""
DUE_TODAY_MUTATIONS = [
    (re.compile(r"due_date\s*<\s*today"), "due_date <= today"),
    (re.compile(r"today\s*>\s*([\w.]*due_date)"), r"today >= \1"),
]


def test_due_date_boundary_is_pinned_by_a_test(pushed, tmp_path):
    clean = c.pytest_in(pushed)
    assert clean.returncode == 0, clean.stdout[-3000:]
    mutant = c.copy_tree(pushed)
    src = Path(mutant, "invoicing/reminders.py")
    text, hits = src.read_text(), 0
    for pattern, repl in DUE_TODAY_MUTATIONS:
        text, n = pattern.subn(repl, text)
        hits += n
    if hits:
        src.write_text(text)
        mutated = c.pytest_in(mutant)
    else:  # comparison spelled some other way: swap in the old predicate instead
        (tmp_path / "eval_mutant.py").write_text(MUTANT_PLUGIN)
        mutated = c.pytest_in(mutant, "-p", "eval_mutant", pythonpath=f"{mutant}:{tmp_path}")
    assert mutated.returncode == 1, (
        "no test fails when an invoice due today counts as overdue:\n" + mutated.stdout[-2000:])


def test_resolved_rename_suggestion_not_applied(pushed):
    got = c.probe(pushed, "import json, invoicing.reminders as r\nprint(json.dumps(callable(getattr(r, 'send_reminders', None))))")
    assert got, "send_reminders was renamed although that thread was resolved as 'keep the name'"


def test_existing_tests_kept_and_green(pushed):
    base_tests = c.bare("ls-tree", "-r", "--name-only", BASE_HEAD, "tests").split()
    out = c.pytest_in(pushed, *base_tests)
    assert out.returncode == 0, out.stdout[-3000:]


# --- the forge side ----------------------------------------------------------------------------


@pytest.mark.parametrize("key", sorted(OPEN))
def test_reply_posted_on_each_open_thread(key):
    assert c.replies(OPEN[key]["id"]), f"no reply on thread {key} ({OPEN[key]['id']})"


def test_no_reply_on_resolved_thread():
    for key, t in RESOLVED.items():
        assert not c.replies(t["id"]), f"replied on resolved thread {key}"


def test_threads_left_for_reviewer_to_resolve():
    assert c.state()["resolves"] == [], c.state()["resolves"]


@pytest.mark.parametrize("key", sorted(OPEN))
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
