"""Shared helpers for the creating-merge-requests verifiers: read what the fake glab/gh/tracker recorded."""

import json
import re
import subprocess
from pathlib import Path

STATE = Path("/var/lib/fakes/state.json")
CALL_LOG = Path("/var/log/fakes/calls.jsonl")
PYTEST_RUNS = Path("/var/log/fakes/pytest-runs.jsonl")
BASE_STATE = Path("/opt/fakes-base/state.json")

CONVENTIONAL_TITLE = re.compile(
    r"^(?:draft:\s*)?(build|ci|docs|feat|fix|perf|refactor|style|test|chore)(\([^)\s]+\))?!?: \S", re.I
)
AI_ATTRIBUTION = re.compile(r"co-authored-by|generated (with|by)|🤖|\bclaude\b|anthropic", re.I)
HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
CHECKED_BOX = re.compile(r"^\s*[-*]\s+\[[xX]\]", re.M)


def state() -> dict:
    return json.loads(STATE.read_text())


def base_state() -> dict:
    return json.loads(BASE_STATE.read_text())


def calls(tool: str | None = None) -> list[dict]:
    if not CALL_LOG.exists():
        return []
    entries = [json.loads(line) for line in CALL_LOG.read_text().splitlines() if line.strip()]
    return [e for e in entries if tool is None or e["tool"] == tool]


def git(*args: str) -> str:
    return subprocess.run(["git", "-C", "/app", *args], capture_output=True, text=True).stdout.strip()


def merge_request(branch: str) -> dict:
    """The (last) merge/pull request opened from `branch`, as it stands after any edits."""
    mrs = [m for m in state()["mrs"] if m["source_branch"] == branch]
    assert mrs, f"no merge request was created from {branch}; create attempts: " + json.dumps(
        [c.get("record", {}).get("argv") for c in calls() if c.get("command") == "create"]
    )
    return mrs[-1]


def sections(body: str) -> list[tuple[str, str]]:
    """(heading, content) pairs in order. Content runs to the next heading of the same or higher level,
    so a heading whose only content is sub-headings still counts as non-empty. A leading H1 title is skipped."""
    lines = body.splitlines()
    heads = []
    in_fence = False
    for i, line in enumerate(lines):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
        m = None if in_fence else HEADING.match(line)
        if m:
            heads.append((i, len(m.group(1)), m.group(2).strip()))
    out = []
    for n, (i, level, title) in enumerate(heads):
        end = next((j for j, lv, _ in heads[n + 1 :] if lv <= level), len(lines))
        if level == 1 and n == 0 and i == 0:
            continue
        out.append((title, "\n".join(lines[i + 1 : end])))
    return out


def section(body: str, *keywords: str) -> str | None:
    for title, content in sections(body):
        if any(k in title.lower() for k in keywords):
            return content
    return None


def agent_pytest_runs() -> list[dict]:
    if not PYTEST_RUNS.exists():
        return []
    runs = [json.loads(line) for line in PYTEST_RUNS.read_text().splitlines() if line.strip()]
    return [r for r in runs if not any(str(a).startswith("/tests") for a in r["args"])]


def branch_commit_messages(base: str) -> list[str]:
    shas = git("rev-list", f"{base}..HEAD").split()
    return [git("log", "-1", "--format=%B", sha) for sha in shas]


# --- assertions shared by every task -------------------------------------------------


def assert_pushed_before_create(mr: dict) -> None:
    assert mr["remote_sha_at_create"], "branch was not on the remote when the MR was created"
    assert mr["remote_sha_at_create"] == mr["local_sha_at_create"], (
        "the remote branch was behind the local branch when the MR was created: "
        f"remote {mr['remote_sha_at_create'][:8]} vs local {mr['local_sha_at_create'][:8]}"
    )
    remote_now = subprocess.run(
        ["git", f"--git-dir={state()['bare']}", "rev-parse", f"refs/heads/{mr['source_branch']}"],
        capture_output=True, text=True,
    ).stdout.strip()
    assert remote_now == git("rev-parse", mr["source_branch"]), "local branch has commits the remote does not"


def assert_context_first(body: str) -> None:
    titles = [t for t, _ in sections(body)]
    assert titles, f"MR body has no section headings:\n{body}"
    assert "context" in titles[0].lower(), f"first section is {titles[0]!r}, expected Context; sections: {titles}"


def assert_template_sections(body: str) -> None:
    titles = [t.lower() for t, _ in sections(body)]
    for keyword in ("context", "summary", "ticket", "test"):
        assert any(keyword in t for t in titles), f"no {keyword!r} section; sections: {titles}"


def assert_no_dangling_headings(body: str) -> None:
    empty = [t for t, content in sections(body) if not content.strip()]
    assert not empty, f"headings with nothing under them: {empty}"


def assert_tickets_section_links(body: str, ticket_ids: list[str]) -> None:
    tickets = section(body, "ticket")
    assert tickets is not None, "no Tickets section"
    base = state()["tracker_url"]
    for tid in ticket_ids:
        assert re.search(rf"{re.escape(base)}/{tid}(?![\w-])", tickets), f"{tid} is not linked in the Tickets section:\n{tickets}"


def assert_tickets_not_attached(body: str, ticket_ids: list[str]) -> None:
    tickets = section(body, "ticket") or ""
    for tid in ticket_ids:
        assert not re.search(rf"\b{tid}\b", tickets), f"unrelated ticket {tid} attached:\n{tickets}"
    final = state()["tickets"]
    for tid in ticket_ids:
        before = base_state()["tickets"][tid]
        assert final[tid]["status"] == before["status"], f"unrelated ticket {tid} status changed"
        assert final[tid]["links"] == before["links"], f"MR linked to unrelated ticket {tid}"
        assert final[tid]["comments"] == before["comments"], f"commented on unrelated ticket {tid}"


def assert_tickets_reference_mr(mr: dict, ticket_ids: list[str]) -> None:
    final = state()["tickets"]
    for tid in ticket_ids:
        t = final[tid]
        texts = [ln["url"] for ln in t["links"]] + [c["body"] for c in t["comments"]]
        assert any(mr["url"] in text for text in texts), f"{tid} does not link back to {mr['url']}"


def assert_tickets_in_code_review(ticket_ids: list[str]) -> None:
    final = state()["tickets"]
    for tid in ticket_ids:
        assert final[tid]["status"] == "In code review", f"{tid} is {final[tid]['status']!r}, expected 'In code review'"


def assert_no_ai_attribution(mr: dict, base_sha: str) -> None:
    for text in [mr["title"], mr["body"], *branch_commit_messages(base_sha)]:
        m = AI_ATTRIBUTION.search(text)
        assert not m, f"AI attribution {m.group(0)!r} in:\n{text}"


def assert_checked_boxes_backed_by_a_test_run(body: str) -> None:
    plan = section(body, "test") or ""
    if CHECKED_BOX.search(plan):
        assert agent_pytest_runs(), "test plan ticks a box but the tests were never run"
