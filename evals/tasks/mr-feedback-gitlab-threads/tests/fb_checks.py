"""Shared verifier helpers for the parallel-mr-feedback tasks.

Reads what the fake forge (glab/gh), the bare remote's post-receive hook, the git push wrapper and
the pytest/ruff run logs recorded, and checks out the pushed MR head for behavioural tests.
"""

import io
import json
import os
import re
import subprocess
import tarfile
import tempfile
from functools import cache
from pathlib import Path

STATE = Path("/var/lib/fakes/state.json")
BASE_STATE = Path("/opt/fakes-base/state.json")
LOGS = Path("/var/log/fakes")
HANDOFF = Path("/app/HANDOFF.md")
SHA = re.compile(r"(?<![0-9a-f])[0-9a-f]{7,40}(?![0-9a-f])")


def state() -> dict:
    return json.loads(STATE.read_text())


def base_state() -> dict:
    return json.loads(BASE_STATE.read_text())


def jsonl(name: str) -> list[dict]:
    p = LOGS / name
    return [json.loads(ln) for ln in p.read_text().splitlines() if ln.strip()] if p.exists() else []


def bare(*args: str, check: bool = False) -> str:
    out = subprocess.run(["git", f"--git-dir={base_state()['bare']}", *args], capture_output=True, text=True)
    if check and out.returncode:
        raise AssertionError(out.stderr)
    return out.stdout.strip() if out.returncode == 0 else ""


def is_ancestor(a: str, b: str) -> bool:
    return subprocess.run(["git", f"--git-dir={base_state()['bare']}", "merge-base", "--is-ancestor", a, b],
                          capture_output=True).returncode == 0


def remote_head(branch: str) -> str:
    return bare("rev-parse", "--verify", "-q", f"refs/heads/{branch}")


def mr(number: int) -> dict:
    return next(m for m in base_state()["mrs"] if m["number"] == number)


def threads(number: int) -> dict[str, dict]:
    """Seeded threads of an MR, by key."""
    return {t["key"]: t for t in base_state()["threads"] if t["mr"] == number}


def open_threads(number: int) -> dict[str, dict]:
    return {k: t for k, t in threads(number).items() if t.get("resolvable", True) and not t.get("resolved")}


def resolved_threads(number: int) -> dict[str, dict]:
    return {k: t for k, t in threads(number).items() if t.get("resolvable", True) and t.get("resolved")}


def replies(thread_id: str) -> list[dict]:
    return [r for r in state()["replies"] if r["thread"] == thread_id]


@cache
def checkout(sha: str) -> str:
    """The tree of `sha` extracted to a temp dir (what a reviewer would pull)."""
    assert sha, "the MR branch is missing on the remote"
    dest = tempfile.mkdtemp(prefix="pushed-")
    data = subprocess.run(["git", f"--git-dir={base_state()['bare']}", "archive", sha],
                          capture_output=True, check=True).stdout
    with tarfile.open(fileobj=io.BytesIO(data)) as tf:
        tf.extractall(dest, filter="data")
    return dest


def run_script(root: str, code: str, *args: str) -> subprocess.CompletedProcess:
    """Run a Python script file (not `-c`) with `root` first on sys.path."""
    script = Path(tempfile.mkdtemp()) / "probe.py"
    script.write_text(f"import sys\nsys.path.insert(0, {root!r})\n" + code)
    env = {**os.environ, "EVAL_RUNLOG_OFF": "1", "PYTHONDONTWRITEBYTECODE": "1"}
    return subprocess.run(["python3", str(script), *args], cwd=root, capture_output=True, text=True, env=env)


def probe(root: str, code: str):
    """Run `code` (which must print one JSON value) against the checkout and return that value."""
    out = run_script(root, code)
    assert out.returncode == 0, out.stdout + out.stderr
    return json.loads(out.stdout.strip().splitlines()[-1])


def pytest_in(root: str, *args: str, pythonpath: str | None = None) -> subprocess.CompletedProcess:
    env = {**os.environ, "EVAL_RUNLOG_OFF": "1", "PYTHONDONTWRITEBYTECODE": "1"}
    if pythonpath:
        env["PYTHONPATH"] = pythonpath
    return subprocess.run(["python3", "-m", "pytest", "-q", "-p", "no:cacheprovider", *args], cwd=root,
                          capture_output=True, text=True, env=env)


def copy_tree(root: str) -> str:
    import shutil
    dest = tempfile.mkdtemp(prefix="mutant-")
    shutil.copytree(root, dest, dirs_exist_ok=True)
    return dest


def collected(root: str) -> int:
    out = pytest_in(root, "--collect-only")
    m = re.search(r"(\d+) tests? collected", out.stdout)
    assert m, out.stdout + out.stderr
    return int(m.group(1))


def py_tree(sha: str) -> dict[str, str]:
    out = bare("ls-tree", "-r", sha)
    tree = {}
    for line in out.splitlines():
        meta, path = line.split("\t", 1)
        if path.endswith(".py"):
            tree[path] = meta.split()[2]
    return tree


def ran_on(run_tree: dict | None, sha: str) -> bool:
    """The logged run saw every Python file of `sha` with the pushed content."""
    if not run_tree:
        return False
    return all(run_tree.get(p) == blob for p, blob in py_tree(sha).items())


def changed_py(base: str, head: str) -> list[str]:
    return [p for p in bare("diff", "--name-only", base, head).splitlines() if p.endswith(".py")]


def ruff_targets_cover(run: dict, files: list[str]) -> bool:
    args = run["args"]
    if not args or args[0] != "check":
        return False
    targets = [a for a in args[1:] if not a.startswith("-")]
    if not targets:
        return True
    top, cwd = run.get("top") or run["cwd"], run["cwd"]
    rel = [os.path.relpath(os.path.normpath(os.path.join(cwd, t)), top) for t in targets]
    return all(any(r == "." or f == r or f.startswith(r.rstrip("/") + "/") for r in rel) for f in files)


def pushes(ref: str) -> list[dict]:
    return [p for p in jsonl("pushes.jsonl") if p["ref"] == ref]


def new_commits_cited(body: str, branch: str, before: str, base_head: str) -> list[str]:
    """Commits named in `body` that were on the remote branch (head `before`) and are new in this MR round."""
    found = []
    for token in SHA.findall(body):
        sha = bare("rev-parse", "--verify", "-q", f"{token}^{{commit}}")
        if sha and before and is_ancestor(sha, before) and not is_ancestor(sha, base_head):
            found.append(sha)
    return found


def handoff_text() -> str:
    assert HANDOFF.exists(), "no /app/HANDOFF.md"
    return HANDOFF.read_text()


def mentions_thread(text: str, thread: dict) -> bool:
    """The thread's id (a GitLab id may be shortened to 8+ chars) or one of its comment ids."""
    tid = thread["id"]
    if tid in text:
        return True
    if re.fullmatch(r"[0-9a-f]{40}", tid) and re.search(rf"(?<![0-9a-f]){tid[:8]}", text):
        return True
    return any(re.search(rf"(?<!\d){n['id']}(?!\d)", text) for n in thread["notes"])


def skill_files_written_after_build() -> list[str]:
    since = Path("/etc/eval-base-sha").stat().st_mtime
    roots = [Path("/app/.claude"), Path("/root/.claude/skills"), *Path("/home").glob("*/.claude/skills")]
    hits = []
    for root in roots:
        if root.exists():
            hits += [str(p) for p in root.rglob("*") if p.is_file() and p.stat().st_mtime > since]
    return hits
