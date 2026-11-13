"""Records each pytest session and ruff run, with the blob of every repo file at that moment.

pytest: loaded as a plugin (entry point), appends to /var/log/fakes/pytest-runs.jsonl.
ruff: the `ruff` on PATH is a wrapper that calls `snapshot()` and appends to ruff-runs.jsonl.
"""

import json
import os
import subprocess
from datetime import UTC, datetime

LOG_DIR = "/var/log/fakes"


def snapshot(cwd: str) -> dict[str, str]:
    """Map each tracked or untracked (not ignored) path in cwd's repo to its current blob sha."""
    top = subprocess.run(["git", "-C", cwd, "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    if top.returncode:
        return {}
    root = top.stdout.strip()
    ls = subprocess.run(["git", "-C", root, "ls-files", "-z", "-co", "--exclude-standard"], capture_output=True, text=True)
    paths = [p for p in ls.stdout.split("\0") if p and os.path.isfile(os.path.join(root, p))]
    if not paths:
        return {}
    out = subprocess.run(["git", "-C", root, "hash-object", "--stdin-paths"], input="\n".join(paths),
                         capture_output=True, text=True)
    return dict(zip(paths, out.stdout.split()))


def record(name: str, entry: dict) -> None:
    if os.environ.get("EVAL_NO_RUNLOG"):
        return
    entry = {"at": datetime.now(UTC).isoformat(), "cwd": os.getcwd(), **entry, "blobs": snapshot(os.getcwd())}
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        with open(f"{LOG_DIR}/{name}", "a") as fh:
            fh.write(json.dumps(entry) + "\n")
    except OSError:
        pass


def pytest_sessionfinish(session, exitstatus):
    record("pytest-runs.jsonl", {"rootdir": str(session.config.rootpath), "args": list(session.config.args),
                                 "exitstatus": int(exitstatus)})
