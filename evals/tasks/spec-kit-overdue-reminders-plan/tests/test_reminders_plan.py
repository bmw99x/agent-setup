"""Verifier: the agent ran the Plan phase on the approved spec and stopped at its approval gate."""

import filecmp
import os
import re
from pathlib import Path

import pytest

APP = Path("/app")
BASE = Path("/opt/base")
FEATURE = APP / "specs/001-overdue-reminders"
PHASE_OUTPUTS = ("specs/", ".specify/", ".claude/", ".git/", "CLAUDE.md", "HANDOFF.md")
SCRATCH = ("__pycache__", ".pytest_cache")
# Runtime packages the project's stack rules out (stdlib-only, cron jobs, outbox for mail).
THIRD_PARTY = re.compile(
    r"\b(celery|apscheduler|redis|rq|dramatiq|huey|sqlalchemy|peewee|requests|httpx|aiohttp|jinja2|"
    r"pydantic|django|flask|fastapi|sendgrid|mailgun|boto3|smtplib)\b",
    re.I,
)


@pytest.fixture(scope="module")
def plan() -> str:
    path = FEATURE / "plan.md"
    assert path.is_file(), "no plan.md beside the approved spec"
    return re.sub(r"<!--.*?-->", "", path.read_text(), flags=re.S)


def _section(text: str, heading: str) -> str:
    match = re.search(rf"^##\s+[^\n]*{heading}[^\n]*\n(.*?)(?=^##\s|\Z)", text, re.M | re.S | re.I)
    return match.group(1) if match else ""


def _field(text: str, name: str) -> str:
    """Value of a `**Name**: value` Technical Context field (to the next bold field or heading)."""
    match = re.search(rf"\*\*{name}\*\*\s*:?\s*(.*?)(?=^\s*[-*]?\s*\*\*[^*\n]+\*\*\s*:|^#|\Z)", text, re.M | re.S | re.I)
    match = match or re.search(rf"^\|\s*\**{name}\**\s*\|\s*(.*?)\|", text, re.M | re.I)  # table layout
    assert match, f"Technical Context has no {name} field"
    return match.group(1).strip()


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


def test_plan_has_mandatory_sections(plan: str):
    for heading in ("Summary", "Technical Context", "Constitution Check", "Project Structure"):
        assert _section(plan, heading).strip(), f"missing or empty plan section: {heading}"


def test_plan_template_placeholders_replaced(plan: str):
    for placeholder in ("[FEATURE]", "[e.g.,", "[REMOVE IF UNUSED]", "Option 1", "[Gates determined", "[link]",
                        "[###-feature"):
        assert placeholder not in plan, f"template placeholder left in plan: {placeholder}"


def test_technical_context_uses_project_python(plan: str):
    assert "3.12" in _field(_section(plan, "Technical Context"), "Language/Version")


def test_technical_context_uses_project_storage(plan: str):
    assert re.search(r"sqlite", _field(_section(plan, "Technical Context"), "Storage"), re.I)


def test_plan_adds_no_third_party_runtime_dependency(plan: str):
    context = _section(plan, "Technical Context")
    try:
        deps = _field(context, "Primary Dependencies")
    except AssertionError:
        deps = context  # field dropped because there are none: then any package named in the context counts
    assert not THIRD_PARTY.search(deps), f"plan brings in a package the project's stack rules out: {deps!r}"


def test_plan_structure_uses_project_job_and_outbox_conventions(plan: str):
    structure = _section(plan, "Project Structure")
    # Either the full path, or a `jobs/` entry in a tree drawn under `app/`.
    in_jobs = "app/jobs/" in structure or re.search(r"^[\s│├└─|`+\\-]*jobs/", structure, re.M)
    assert in_jobs, "reminder run is not planned as a job in app/jobs/"
    # The notifier is reused, not modified, so the tree need not list it: look anywhere past the Summary.
    rest = plan.replace(_section(plan, "Summary"), "", 1)
    assert re.search(r"notifications\.py|OutboxNotifier|\boutbox\b", rest, re.I), \
        "reminders not planned through the existing outbox notifier"


def test_stopped_at_plan_gate_no_tasks():
    tasks = [p.relative_to(APP).as_posix() for p in APP.rglob("tasks.md") if ".git" not in p.parts]
    assert not tasks, f"tasks written before the plan was approved: {tasks}"


def test_stopped_at_plan_gate_no_code_changes():
    base, now = _tree(BASE), _tree(APP)
    added = sorted(set(now) - set(base))
    removed = sorted(set(base) - set(now))
    changed = sorted(p for p in set(base) & set(now) if not filecmp.cmp(base[p], now[p], shallow=False))
    assert not (added or removed or changed), f"added={added} removed={removed} changed={changed}"


def test_handoff_points_to_plan_for_approval():
    handoff = APP / "HANDOFF.md"
    assert handoff.is_file(), "no /app/HANDOFF.md"
    assert "plan.md" in handoff.read_text(), "HANDOFF.md does not point at the plan to review"
