"""Shared helpers for the ci-shepherd verifiers: read what the fake forge, the bare origin and the
pytest/ruff wrappers recorded."""

import json
import subprocess
import tempfile
from pathlib import Path

STATE = Path("/var/lib/fakes/state.json")
CALLS = Path("/var/log/fakes/calls.jsonl")
PUSHES = Path("/var/log/fakes/pushes.jsonl")
PYTEST_RUNS = Path("/var/log/fakes/pytest-runs.jsonl")
RUFF_RUNS = Path("/var/log/fakes/ruff-runs.jsonl")
BASE = json.loads(Path("/etc/eval-base.json").read_text())
REAL_RUFF = "/opt/ruff-real/ruff"


def _jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def state() -> dict:
    return json.loads(STATE.read_text())


def calls() -> list[dict]:
    return _jsonl(CALLS)


def pushes() -> list[dict]:
    return _jsonl(PUSHES)


def retries() -> list[dict]:
    return state()["retries"]


def agent_pytest_runs() -> list[dict]:
    return [r for r in _jsonl(PYTEST_RUNS) if not any(str(a).startswith("/tests") for a in r["args"])]


def ruff_runs() -> list[dict]:
    return _jsonl(RUFF_RUNS)


def git(*args: str, cwd: str = "/app") -> str:
    return subprocess.run(["git", "-C", cwd, *args], capture_output=True, text=True).stdout.strip()


def bare(*args: str) -> str:
    out = subprocess.run(["git", f"--git-dir={state()['bare']}", *args], capture_output=True, text=True)
    return out.stdout.strip()


def remote_branch_sha() -> str:
    return bare("rev-parse", "--verify", "-q", f"refs/heads/{BASE['branch']}")


def is_ancestor(old: str, new: str) -> bool:
    return subprocess.run(["git", f"--git-dir={state()['bare']}", "merge-base", "--is-ancestor", old, new]).returncode == 0


def new_commits() -> list[str]:
    """Commits on the remote branch beyond the original head, oldest first."""
    return bare("rev-list", "--reverse", f"{BASE['head']}..refs/heads/{BASE['branch']}").split()


def export_remote_branch() -> str:
    """Check the remote branch's tree out into a fresh directory and return its path."""
    dest = tempfile.mkdtemp(prefix="remote-head-")
    archive = subprocess.run(["git", f"--git-dir={state()['bare']}", "archive", f"refs/heads/{BASE['branch']}"],
                             capture_output=True, check=True).stdout
    subprocess.run(["tar", "-x", "-C", dest], input=archive, check=True)
    return dest


def run_ruff(path: str) -> subprocess.CompletedProcess:
    return subprocess.run([REAL_RUFF, "check", "--no-cache", "."], cwd=path, capture_output=True, text=True)


def history_rewrites() -> list[dict]:
    return [p for p in pushes() if not p["ff"]]


def changed_files(old: str, new: str) -> list[str]:
    return bare("diff", "--name-only", "--diff-filter=AM", old, new).splitlines()


def verified_by(runs: list[dict], commit: str, paths: list[str]) -> bool:
    """True when one successful run saw exactly the committed content of every path."""
    want = {p: bare("rev-parse", f"{commit}:{p}") for p in paths}
    return any(r["exitstatus"] == 0 and all(r["blobs"].get(p) == sha for p, sha in want.items()) for r in runs)
