import re
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
from _brief import DATED_DIR, VAGUE_REOPEN, column, new_dirs, output_dir, read, row_matching, section, word_count  # noqa: E402

BASE = Path("/etc/eval-base-sha").read_text().strip()


def git(*args):
    return subprocess.run(["git", "-C", "/app", *args], capture_output=True, text=True, check=True).stdout


@pytest.fixture(scope="module")
def brief():
    return read(output_dir() / "brief.md")


@pytest.fixture(scope="module")
def journal():
    path = output_dir() / "journal.md"
    assert path.is_file(), f"{path} missing"
    return read(path)


def test_output_is_one_dated_housekeeping_dir_with_brief_and_journal():
    dirs = new_dirs()
    assert len(dirs) == 1, f"expected one dir under /app/.claude/housekeeping, got {dirs}"
    assert DATED_DIR.match(dirs[0].name), f"{dirs[0].name} is not <YYYY-MM-DD>-<slug>"
    assert {"brief.md", "journal.md"} <= {p.name for p in dirs[0].iterdir()}


def test_brief_is_at_most_400_words(brief):
    assert word_count(brief) <= 400, f"brief has {word_count(brief)} words"


def test_goal_quotes_the_users_words(brief):
    assert re.search(r"before 06:00", section(brief, "goal"))


def test_sftp_limit_is_a_constraint_with_source_and_checkable_reopen(brief):
    body = section(brief, "constraint")
    row = row_matching(body, r"2\s?GB")
    assert re.search(r"contract|bank", " ".join(row), re.IGNORECASE), row
    reopen = column(body, row, "reopen")
    assert not VAGUE_REOPEN.search(reopen), f"vague Reopen if: {reopen!r}"


def test_laptop_timing_is_scoped_to_its_dataset_and_environment(brief):
    row = " ".join(row_matching(section(brief, "measured"), r"\b41\b"))
    assert re.search(r"laptop", row, re.IGNORECASE), row
    assert re.search(r"sqlite", row, re.IGNORECASE), row


def test_copy_speedup_is_an_untested_claim_not_a_measurement(brief):
    assert re.search(r"\bCOPY\b", section(brief, "untested"))
    assert not re.search(r"\bCOPY\b|10\s?x", section(brief, "measured"))


def test_parked_worker_pool_has_checkable_reopen_condition(brief):
    body = section(brief, "closed")
    row = row_matching(body, r"worker|parallel")
    reopen = column(body, row, "reopen")
    assert not VAGUE_REOPEN.search(reopen), f"vague Reopen if: {reopen!r}"


def test_journal_records_the_bottleneck_assumption_flip(journal):
    assumptions = section(journal, "assumption")
    assert re.search(r"quer|select|database|\bdb\b", assumptions, re.IGNORECASE), assumptions
    assert re.search(r"render|pdf", assumptions, re.IGNORECASE), assumptions


def test_nothing_committed_and_tracked_files_untouched():
    assert git("rev-parse", "HEAD").strip() == BASE, "committing is the user's call"
    assert git("diff", "--name-only", BASE) == "", "tracked files changed"
