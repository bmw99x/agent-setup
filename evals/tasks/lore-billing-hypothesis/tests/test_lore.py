"""Verifier for lore-billing-hypothesis: a repo-local conventions skill derived from code + MR history."""

import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, "/tests")
import lore  # noqa: E402

REPO = "billing"
CONVENTIONS = {
    "money_is_int_minor_units": [r"minor|amount_minor|total_minor|cents|pence", r"\bint\b|integer"],
    "module_functions_not_service_classes": [r"function", r"service"],
    "external_sdks_behind_adapters": [r"adapter", r"\bsdks?\b|stripe|xero|gocardless|postmark|external|third.?party|vendor|provider"],
    "timestamps_are_aware_utc": [r"\butc\b", r"datetime|timestamp|\btime"],
}
RED_HERRING = r"\bprint\b"
GLOSSARY_TERMS = [r"invoice", r"credit[ _-]?note", r"dunning", r"settle", r"payout"]
YES_NO = re.compile(r"^(any|is|are|does|do|did|has|have|can|could|should|will|would|was|were|must|may)\b", re.I)
SUMMARY = Path("/app/LORE_SUMMARY.md")
CONTRADICTS = (r"\bnot\b|n't|\bmore\b|increas|\bgrew\b|grown|\brose\b|risen|\bup\b|opposite|contrar|\bfalse\b|"
               r"doesn.?t hold|\bwrong\b|\brather\b|\bgrow")
CONFIRMS = (r"fewer|\bdown\b|decreas|dropp|\bholds?\b|\btrue\b|confirm|correct|\bgone\b|removed|retired|"
            r"from \d+ to \d|\d+\s*(→|->)\s*\d|shrank|reduc")


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


def test_reviewer_rejected_print_logging_not_a_rule(its):
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


def test_readme_drift_recorded_with_check_date(skill):
    drift = skill / "references" / "readme-drift.md"
    assert drift.is_file(), "no references/readme-drift.md"
    text = drift.read_text()
    assert re.search(r"decimal", text, re.I), "README's Decimal-money claim not listed as drift"
    assert re.search(r"service", text, re.I), "README's service-classes claim not listed as drift"
    assert re.search(r"\b20\d\d-\d\d-\d\d\b", text), "no check date in readme-drift.md"


def test_readme_decimal_claim_not_a_rule(its):
    assert lore.affirmed_as_rule(its, r"\bdecimal\b") == []


@pytest.fixture(scope="module")
def summary():
    assert SUMMARY.is_file(), "no /app/LORE_SUMMARY.md"
    return lore.items(SUMMARY)


def test_hypothesis_adapter_half_contradicted_with_counts(summary):
    hits = [i.text for i in summary if lore.matches(i.text, [r"adapter", r"\d", CONTRADICTS])]
    assert hits, "no counted verdict that adapters did not go away"


def test_hypothesis_service_class_half_confirmed_with_counts(summary):
    hits = [i.text for i in summary if lore.matches(i.text, [r"service", r"\d", CONFIRMS])]
    assert hits, "no counted verdict that service classes went away"
