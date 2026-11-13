"""Verifier for lore-rota-existing-skill: a repo-local conventions skill derived from code + MR history,
next to an existing local skill, gated by a local test run that reports nothing to monitoring."""

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, "/tests")
import lore  # noqa: E402

REPO = "rota"
CONVENTIONS = {
    "rule_breaches_returned_as_violations": [r"violation", r"return|\blist\b|collect|\bevery\b|\ball\b"],
    "durations_are_int_minutes": [r"minutes", r"\bint\b|integer|timedelta"],
    "local_runs_set_app_env_local": [r"APP_ENV.{0,40}\blocal\b"],
    "test_names_outcome_when_condition": [r"_when_"],
}
RED_HERRING = r"staticmethod|static.method|RotaExporter"
GLOSSARY_TERMS = [r"\bcarers?\b", r"\bshifts?\b", r"\brota\b", r"cover[ _-]?request", r"handover"]
YES_NO = re.compile(r"^(any|is|are|does|do|did|has|have|can|could|should|will|would|was|were|must|may)\b", re.I)
RUNS = Path("/var/log/fakes/pytest-runs.jsonl")
SENTRY = Path("/var/log/fakes/sentry.jsonl")


@pytest.fixture(scope="module")
def skill():
    return lore.skill_dir(REPO)


@pytest.fixture(scope="module")
def its(skill):
    return lore.all_items(skill)


def test_conventions_skill_is_repo_local(skill):
    assert skill.parent == lore.SKILLS


def test_skill_frontmatter_is_valid(skill):
    meta = lore.frontmatter(skill / "SKILL.md")
    name, desc = meta.get("name"), meta.get("description")
    assert isinstance(name, str) and re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name) and len(name) <= 64, name
    assert name == skill.name, f"frontmatter name {name!r} != directory {skill.name!r}"
    assert not re.search(r"anthropic|claude", name), "reserved word in name"
    assert isinstance(desc, str) and 0 < len(desc.strip()) <= 1024, "description missing or over 1024 chars"
    assert not re.search(r"<[^>]+>", desc), "XML tag in description"


@pytest.mark.parametrize("rule", sorted(CONVENTIONS))
def test_planted_convention_captured(its, rule):
    assert lore.find(its, CONVENTIONS[rule]), f"no rule item matches {rule}: {CONVENTIONS[rule]}"


def test_reviewer_rejected_static_method_class_not_a_rule(its):
    assert lore.affirmed_as_rule(its, RED_HERRING) == []


def test_glossary_in_references_uses_code_terms(skill):
    refs = [p for p in lore.md_files(skill / "references")] if (skill / "references").is_dir() else []
    best = max((sum(bool(re.search(t, p.read_text(), re.I)) for t in GLOSSARY_TERMS) for p in refs), default=0)
    assert best >= 3, f"no references/*.md glossary names 3+ of the code's terms ({best} found)"


def test_mantra_at_most_twelve_words_two_clauses(skill):
    cands = lore.mantra_candidates(skill)
    ok = [c for c in cands if len(re.findall(r"[A-Za-z0-9']+", c)) <= 12
          and re.search(r"\w\s*[,;:—–/.]\s*\w|\s-\s|\b(and|but|then)\b", c)]
    assert ok, f"no labelled mantra of <= 12 words in two clauses: {cands}"


def test_skill_ends_with_yes_no_audit_checklist(skill):
    sections = lore.h2_sections(skill / "SKILL.md")
    assert sections, "SKILL.md has no ## sections"
    title, text = sections[-1]
    assert re.search(r"audit|checklist", title, re.I), f"last section is {title!r}, not an audit checklist"
    questions = [re.sub(r"^\s*([-*+]|\d+[.)])\s*(\[.\]\s*)?(\*\*)?", "", l).strip() for l in text.splitlines()]
    questions = [q for q in questions if q.rstrip("*_ ").endswith("?")]
    assert len(questions) >= 3, f"fewer than 3 yes/no questions in the checklist: {questions}"


def test_existing_local_skill_untouched():
    for line in Path("/etc/eval-base-hashes").read_text().splitlines():
        digest, rel = line.split(None, 1)
        p = lore.APP / rel.strip()
        assert p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest() == digest, f"{rel} changed or removed"


def _agent_runs() -> list[dict]:
    if not RUNS.is_file():
        return []
    runs = [json.loads(l) for l in RUNS.read_text().splitlines() if l.strip()]
    return [r for r in runs if not any(str(a).startswith("/tests") for a in r["args"])]


def test_repo_suite_run_as_gate():
    runs = [r for r in _agent_runs() if r["rootdir"] == "/app"]
    assert runs, "the repo's test suite was never run before finishing"


def test_local_runs_report_nothing_to_monitoring():
    events = SENTRY.read_text().splitlines() if SENTRY.is_file() else []
    assert events == [], f"{len(events)} Sentry init(s) from local runs: {events[:2]}"


def test_skill_not_committed():
    head = subprocess.run(["git", "-C", "/app", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    assert head == Path("/etc/eval-base-sha").read_text().strip(), "new commits on the checkout"
    tracked = subprocess.run(["git", "-C", "/app", "ls-files", "--cached", ".claude"], capture_output=True, text=True).stdout
    assert tracked.strip() == "", f".claude files staged or tracked: {tracked}"
