"""Content fingerprint of a checkout's Python files: {repo-relative path: git blob sha}.

Shared by the pytest and ruff run logs, so the verifier can tell which tree a gate ran on
(a worktree, uncommitted edits, the pushed commit) by comparing with `git ls-tree` of a commit.
"""

import subprocess


def toplevel(path: str) -> str | None:
    out = subprocess.run(["git", "-C", path, "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    return out.stdout.strip() if out.returncode == 0 else None


def py_blobs(path: str) -> dict[str, str] | None:
    top = toplevel(path)
    if top is None:
        return None
    files = subprocess.run(["git", "-C", top, "ls-files", "-co", "--exclude-standard", "--", "*.py"],
                           capture_output=True, text=True)
    if files.returncode:
        return None
    names = [f for f in files.stdout.splitlines() if f]
    if not names:
        return {}
    out = subprocess.run(["git", "-C", top, "hash-object", "--", *names], capture_output=True, text=True)
    return dict(zip(names, out.stdout.split())) if out.returncode == 0 else None
