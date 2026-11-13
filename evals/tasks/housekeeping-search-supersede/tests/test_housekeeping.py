import re
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
from _brief import DATED_DIR, VAGUE_REOPEN, column, new_dirs, output_dir, read, row_matching, section, word_count  # noqa: E402

BASE = Path("/etc/eval-base-sha").read_text().strip()
OLD = "2026-10-01-search-ranking"


def git(*args):
    return subprocess.run(["git", "-C", "/app", *args], capture_output=True, text=True, check=True).stdout


@pytest.fixture(scope="module")
def brief():
    return read(output_dir(existing=(OLD,)) / "brief.md")


def test_new_brief_and_journal_go_in_a_new_dated_dir():
    dirs = new_dirs(existing=(OLD,))
    assert len(dirs) == 1, f"expected one new dir beside {OLD}, got {dirs}"
    assert DATED_DIR.match(dirs[0].name), f"{dirs[0].name} is not <YYYY-MM-DD>-<slug>"
    assert {"brief.md", "journal.md"} <= {p.name for p in dirs[0].iterdir()}


def test_header_names_the_superseded_brief(brief):
    header = "\n".join(brief.splitlines()[:6])
    assert re.search(r"supersed", header, re.IGNORECASE), header
    assert OLD in header, header


def test_october_brief_and_journal_are_kept_unchanged():
    result = subprocess.run(["sha256sum", "-c", "/etc/eval-old-housekeeping.sha256"], cwd="/app",
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr


def test_brief_is_at_most_400_words(brief):
    assert word_count(brief) <= 400, f"brief has {word_count(brief)} words"


def test_users_laptop_load_test_is_tagged_user_reported(brief):
    row = " ".join(row_matching(brief, r"180"))
    assert re.search(r"user[- ]reported", row, re.IGNORECASE), row


def test_elasticsearch_rejection_is_settled_by_preference(brief):
    body = section(brief, "closed")
    row = row_matching(body, r"elastic")
    settled = column(body, row, "settled")
    assert re.search(r"preference", settled, re.IGNORECASE), f"Settled by: {settled!r}"


def test_typesense_claim_is_untested_not_measured(brief):
    assert re.search(r"typesense", section(brief, "untested"), re.IGNORECASE)
    assert not re.search(r"typesense", section(brief, "measured"), re.IGNORECASE)


def test_parked_learning_to_rank_has_checkable_reopen_condition(brief):
    body = section(brief, "closed")
    row = row_matching(body, r"learning[- ]to[- ]rank|\bltr\b")
    reopen = column(body, row, "reopen")
    assert not VAGUE_REOPEN.search(reopen), f"vague Reopen if: {reopen!r}"


def test_nothing_committed_and_tracked_files_untouched():
    assert git("rev-parse", "HEAD").strip() == BASE, "committing is the user's call"
    assert git("diff", "--name-only", BASE) == "", "tracked files changed"
