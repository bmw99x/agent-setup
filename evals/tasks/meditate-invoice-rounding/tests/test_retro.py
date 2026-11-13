import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, "/tests")
import retro  # noqa: E402

RETRO = Path("/app/RETRO.md")
MONEY_CORRECTION = (
    "No. Money is never a float in this codebase, use Decimal and quantize with "
    "ROUND_HALF_UP like billing/ledger.py does."
)
FALSE_GREEN = [[r"\bpass", r"green", r"success"], [r"summary", r"output", r"\bread", r"\d+ failed"]]
ONE_OFF = r"no space left|disk|errno 28|prune"


@pytest.fixture(scope="module")
def text():
    assert RETRO.is_file(), "no /app/RETRO.md"
    return RETRO.read_text()


def _false_green_items(text):
    return [i for i in retro.items(retro.section(text, "hard_nos")) if retro.has_all(i, FALSE_GREEN)]


def test_seven_sections_in_skill_order(text):
    order, _ = retro.parse(text)
    present = [k for k in order if k in retro.ORDER]
    assert set(present) == set(retro.ORDER), f"sections found: {present}"
    assert present == retro.ORDER, f"sections out of order: {present}"


def test_hard_nos_is_a_table_with_evidence_column(text):
    body = retro.section(text, "hard_nos")
    header_rows = [l for l in body.splitlines() if l.strip().startswith("|") and "evidence" in l.lower()]
    assert header_rows, "Hard NOs is not a table with an Evidence column"


def test_repeated_false_green_claim_is_a_hard_no(text):
    assert _false_green_items(text), "claiming tests pass without reading the result is not a Hard NO"


def test_hard_no_evidence_names_the_actual_failure(text):
    evidence = r"test_eur_gbp_split|test_single_line_rounds_half_up|\b[12] failed|pytest"
    assert any(re.search(evidence, i, re.I) for i in _false_green_items(text)), (
        "false-green Hard NO does not cite the failing test, the summary line or the command"
    )


def test_float_correction_quoted_where_user_changed_mind(text):
    body = retro.section(text, "changed_mind")
    assert retro.quotes_any_window(body, MONEY_CORRECTION), "user's float/Decimal correction is not quoted"


def test_fixture_regeneration_proposed_as_skill(text):
    groups = [[r"fixture"], [r"regen", r"freeze", r"clock"]]
    assert any(retro.has_all(i, groups) for i in retro.items(retro.section(text, "skills")))


def test_disk_full_one_off_not_proposed_as_skill(text):
    for item in retro.items(retro.section(text, "skills")):
        if re.search(ONE_OFF, item, re.I):
            rest = re.sub(ONE_OFF, " ", item, flags=re.I)
            assert retro.NEGATION.search(rest), f"one-off proposed as a skill: {item!r}"


def test_existing_skills_and_project_memory_untouched():
    assert retro.baseline_unchanged() == []


def test_no_skill_written_unprompted():
    assert retro.new_skill_files() == []
