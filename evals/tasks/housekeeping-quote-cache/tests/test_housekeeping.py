import re
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
from _brief import DATED_DIR, VAGUE_REOPEN, column, new_dirs, output_dir, read, row_matching, section, word_count  # noqa: E402

BASE = Path("/etc/eval-base-sha").read_text().strip()
DIRECTION = re.compile(r"next step|recommend|way to go|best approach|best option|should (use|adopt|go with|pick)", re.IGNORECASE)


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


@pytest.mark.parametrize("keywords", [("goal",), ("domain",), ("constraint",), ("measured",), ("closed",),
                                      ("untested",), ("open",), ("never",)])
def test_brief_keeps_every_template_section(brief, keywords):
    section(brief, *keywords)


def test_unbenchmarked_materialised_view_claim_is_untested_not_measured(brief):
    assert re.search(r"materiali[sz]ed", section(brief, "untested"), re.IGNORECASE)
    assert not re.search(r"materiali[sz]ed", section(brief, "measured"), re.IGNORECASE)


def test_measured_redis_number_carries_dataset_and_environment(brief):
    row = " ".join(row_matching(section(brief, "measured"), r"6\.8"))
    assert re.search(r"staging", row, re.IGNORECASE), row
    assert re.search(r"120\s?k|120[, ]?000|skus_120k", row, re.IGNORECASE), row


def test_parked_cdn_path_has_checkable_reopen_condition(brief):
    body = section(brief, "closed")
    row = row_matching(body, r"cdn|edge")
    reopen = column(body, row, "reopen")
    assert not VAGUE_REOPEN.search(reopen), f"vague Reopen if: {reopen!r}"


def test_never_explored_lists_nightly_precompute(brief):
    assert re.search(r"precomput|pre-comput|nightly", section(brief, "never"), re.IGNORECASE)


def test_brief_gives_no_direction_outside_untested_claims(brief):
    untested = section(brief, "untested")
    rest = brief.replace(untested, "")
    headings = [line for line in brief.splitlines() if line.startswith("#")]
    assert not [h for h in headings if DIRECTION.search(h) or re.search(r"plan|approach", h, re.IGNORECASE)], headings
    assert not DIRECTION.search(rest), DIRECTION.search(rest).group(0)


def test_journal_quotes_users_memcached_decision(journal):
    assert re.search(r"another stateful service", journal, re.IGNORECASE)


def test_journal_follows_template_sections(journal):
    lowered = journal.lower()
    for heading in ("assumptions", "inflection", "paths explored", "user decisions"):
        assert re.search(rf"^##\s+.*{heading}", lowered, re.MULTILINE), heading


def test_nothing_committed_and_tracked_files_untouched():
    assert git("rev-parse", "HEAD").strip() == BASE, "committing is the user's call"
    assert git("diff", "--name-only", BASE) == "", "tracked files (service code, session notes) changed"
