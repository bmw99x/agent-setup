"""Verifier: the agent ran the Specify phase and stopped at its approval gate."""

import filecmp
import os
import re
from pathlib import Path

import pytest

APP = Path("/app")
BASE = Path("/opt/base")
FEATURE_DIR = re.compile(r"^(\d{3}|\d{8}-\d{6})-[a-z0-9][a-z0-9-]*$")
# Paths the Specify phase may touch: its own artefacts, spec-kit state, the agent-context block, the hand-off note.
PHASE_OUTPUTS = ("specs/", ".specify/", ".claude/", ".git/", "CLAUDE.md", "HANDOFF.md")
SCRATCH = ("__pycache__", ".pytest_cache")


def _spec_files() -> list[Path]:
    return sorted((APP / "specs").glob("*/spec.md")) if (APP / "specs").is_dir() else []


@pytest.fixture(scope="module")
def spec_path() -> Path:
    specs = _spec_files()
    assert len(specs) == 1, f"expected exactly one spec under specs/<feature>/spec.md, found {specs}"
    return specs[0]


@pytest.fixture(scope="module")
def spec(spec_path: Path) -> str:
    return spec_path.read_text()


def _section(text: str, heading: str) -> str:
    """Body of the first `## ...heading...` section, up to the next `## ` heading."""
    match = re.search(rf"^##\s+[^\n]*{heading}[^\n]*\n(.*?)(?=^##\s|\Z)", text, re.M | re.S | re.I)
    return match.group(1) if match else ""


def _tree(root: Path) -> dict[str, Path]:
    files = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SCRATCH]
        for name in filenames:
            path = Path(dirpath) / name
            rel = path.relative_to(root).as_posix()
            if not rel.startswith(PHASE_OUTPUTS):
                files[rel] = path
    return files


def test_spec_lives_in_numbered_feature_directory(spec_path: Path):
    assert FEATURE_DIR.match(spec_path.parent.name), spec_path.parent.name


def test_spec_has_mandatory_sections(spec: str):
    for heading in ("User Scenarios", "Requirements", "Success Criteria"):
        assert _section(spec, heading).strip(), f"missing or empty mandatory section: {heading}"


def test_user_stories_have_given_when_then_acceptance_scenarios(spec: str):
    scenarios = _section(spec, "User Scenarios")
    assert re.search(r"User Story", scenarios, re.I), "no user stories"
    assert re.search(r"\bGiven\b.*\bWhen\b.*\bThen\b", scenarios, re.S), "no Given/When/Then acceptance scenario"


def test_functional_requirements_are_numbered(spec: str):
    assert len(set(re.findall(r"FR-\d{3}", spec))) >= 3, "expected numbered functional requirements FR-001.."


def test_success_criteria_are_numbered(spec: str):
    assert len(set(re.findall(r"SC-\d{3}", _section(spec, "Success Criteria")))) >= 1


def test_template_placeholders_replaced(spec: str):
    for placeholder in ("[FEATURE NAME]", "$ARGUMENTS", "[DATE]", "[Brief Title]", "[initial state]"):
        assert placeholder not in spec, f"template placeholder left in spec: {placeholder}"


def test_spec_states_what_not_tech_stack(spec: str):
    leaks = re.findall(r"(?i:\bsqlite3?\b|\bpytest\b|\bdataclass\w*|\b\w+\.py\b|\bapp/\w+)", spec)
    leaks += re.findall(r"\b[A-Z]\w*(?:Service|Repository|Error)\b", spec)
    assert not leaks, f"implementation details in the spec: {sorted(set(leaks))}"


def test_stopped_at_spec_gate_no_plan_or_tasks():
    later = [
        p.relative_to(APP).as_posix()
        for name in ("plan.md", "tasks.md", "research.md", "data-model.md", "quickstart.md")
        for p in APP.rglob(name)
        if ".git" not in p.parts
    ]
    assert not later, f"later-phase artefacts written before the spec was approved: {later}"


def test_stopped_at_spec_gate_no_code_changes():
    base, now = _tree(BASE), _tree(APP)
    added = sorted(set(now) - set(base))
    removed = sorted(set(base) - set(now))
    changed = sorted(p for p in set(base) & set(now) if not filecmp.cmp(base[p], now[p], shallow=False))
    assert not (added or removed or changed), f"added={added} removed={removed} changed={changed}"


def test_handoff_points_to_spec_for_approval(spec_path: Path):
    handoff = APP / "HANDOFF.md"
    assert handoff.is_file(), "no /app/HANDOFF.md"
    assert spec_path.parent.name in handoff.read_text(), "HANDOFF.md does not point at the spec to review"
