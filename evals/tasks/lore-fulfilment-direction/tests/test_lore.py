"""Verifier for lore-fulfilment-direction: a repo-local conventions skill derived from code + MR history."""

import re
import sys

import pytest

sys.path.insert(0, "/tests")
import lore  # noqa: E402

REPO = "fulfilment"
CONVENTIONS = {
    "money_is_int_pence": [r"pence", r"\bint\b|integer|float|decimal"],
    "io_only_in_gateways": [r"gateway", r"\bI/?O\b|http|sql|database|network|side.?effect|\bpure\b"],
    "failures_raise_fulfilment_error": [r"rais|fail(s|ing)? loud|exception", r"\bNone\b|FulfilmentError"],
    "tests_pass_fakes_not_patches": [r"\bfakes?\b|tests/fakes", r"mock|patch"],
    "read_then_decide_then_write": [r"\bread", r"\bwrit", r"decid|decision|\bpure\b"],
}
RED_HERRING = r"\bABCs?\b|abstract base|BaseGateway|abc\.ABC|abstractmethod"
DIRECTION = [r"gateway", r"constructor|__init__|inject|\bhand(s|ed)?\b|passed in|receiv|takes? (its|their|a)\b",
             r"client|connection"]
GLOSSARY_TERMS = [r"consignment", r"pick[ _-]?list", r"despatch", r"\bbays?\b", r"pick[ _-]?line"]
YES_NO = re.compile(r"^(any|is|are|does|do|did|has|have|can|could|should|will|would|was|were|must|may)\b", re.I)


@pytest.fixture(scope="module")
def skill():
    return lore.skill_dir(REPO)


@pytest.fixture(scope="module")
def its(skill):
    return lore.all_items(skill)


def _tag(item: lore.Item) -> str:
    return (item.text + " " + item.heading).lower()


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


def test_reviewer_rejected_abc_base_class_not_a_rule(its):
    assert lore.affirmed_as_rule(its, RED_HERRING) == []


def test_glossary_in_references_uses_code_terms(skill):
    refs = [p for p in lore.md_files(skill / "references")] if (skill / "references").is_dir() else []
    best = max((sum(bool(re.search(t, p.read_text(), re.I)) for t in GLOSSARY_TERMS) for p in refs), default=0)
    assert best >= 3, f"no references/*.md glossary names 3+ of the code's terms ({best} found)"


def test_drifting_synonym_mapped_to_canonical_term(its):
    rows = [i for i in its if lore.matches(i.text, [r"shipment", r"consignment"]) and re.search(r"\||→|->|=>", i.text)]
    assert rows, "no synonyms row mapping 'shipment' to 'consignment'"


def test_direction_mr_rule_tagged_direction(its):
    hits = lore.find(its, DIRECTION)
    assert any("[direction]" in _tag(i) for i in hits), "open MR !31's gateway-constructor rule is not tagged [direction]"
    assert not [i.text for i in hits if "[landed]" in i.text.lower() and "[direction]" not in i.text.lower()]


def test_landed_rule_tagged_landed(its):
    hits = lore.find(its, CONVENTIONS["money_is_int_pence"])
    assert any("[landed]" in _tag(i) for i in hits), "the int-pence rule is not tagged [landed]"


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
