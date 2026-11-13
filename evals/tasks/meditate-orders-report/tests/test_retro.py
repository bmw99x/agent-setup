import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, "/tests")
import retro  # noqa: E402

REFLECTION = Path("/app/REFLECTION.md")
CACHE_CORRECTION = (
    "Right problem, wrong fix — a cache just hides the N+1. "
    "Load customers with selectinload in the repository query."
)
LAST_FAILED = r"--lf\b|last[\s-]?failed"
CONTRADICTED = (
    r"contradict|\bhid|\bhide|miss|caught|\bnot\b|n't|never|\bbut\b|avoid|instead|\bonly\b|\bred\b|"
    r"drop|except|unless|full suite|whole suite|before push|ci\b|test_invoice_export_totals"
)
USE_WHEN = r"use (it |this )?(when|for|if|on)|when to use|applies (when|to)|good for|use case|\bwhen:"
NOT_WHEN = (
    r"when not|not when|don'?t use|do not use|avoid (it |this )?(when|for|on)|skip (it |this )?(when|for|on)|"
    r"not for|not (worth|needed|useful)|unless|doesn'?t apply|not on|\bnot:"
)
ONE_OFF = r"clock|certificate|ssl|tls|flight"


@pytest.fixture(scope="module")
def text():
    assert REFLECTION.is_file(), "no /app/REFLECTION.md"
    return REFLECTION.read_text()


def test_running_tests_from_subdirectory_is_a_hard_no(text):
    groups = [[r"conftest", r"repo root", r"root", r"cwd", r"working directory", r"db_session", r"subdir", r"cd reports"]]
    assert any(retro.has_all(i, groups) for i in retro.items(retro.section(text, "hard_nos")))


def test_cache_correction_quoted_where_user_changed_mind(text):
    body = retro.section(text, "changed_mind")
    assert retro.quotes_any_window(body, CACHE_CORRECTION), "user's cache-vs-selectinload correction is not quoted"


def test_positive_patterns_state_when_to_use_and_when_not(text):
    body = retro.section(text, "positive").lower()
    assert re.search(USE_WHEN, body), "positive patterns give no 'use when'"
    assert re.search(NOT_WHEN, body), "positive patterns give no 'when not to'"


def test_contradicted_last_failed_tip_not_kept_as_positive_pattern(text):
    for item in retro.items(retro.section(text, "positive")):
        if re.search(LAST_FAILED, item, re.I):
            rest = re.sub(LAST_FAILED, " ", item, flags=re.I)
            assert re.search(CONTRADICTED, rest, re.I), f"--lf kept as an unqualified positive pattern: {item!r}"


def test_report_snapshot_workflow_proposed_as_skill(text):
    groups = [[r"snapshot"]]
    assert any(retro.has_all(i, groups) for i in retro.items(retro.section(text, "skills")))


def test_clock_one_off_not_proposed_as_skill(text):
    for item in retro.items(retro.section(text, "skills")):
        if re.search(ONE_OFF, item, re.I):
            rest = re.sub(ONE_OFF, " ", item, flags=re.I)
            assert retro.NEGATION.search(rest), f"one-off proposed as a skill: {item!r}"


def test_existing_skills_and_project_memory_untouched():
    assert retro.baseline_unchanged() == []


def test_no_skill_written_unprompted():
    assert retro.new_skill_files() == []
