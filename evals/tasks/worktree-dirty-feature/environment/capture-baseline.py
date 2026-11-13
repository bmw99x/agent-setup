"""Record the repo's pre-task state in a root-owned file the verifier trusts."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(sys.argv[1])
OUT = Path("/etc/eval-base.json")


def git(*args):
    return subprocess.run(["git", "-C", str(REPO), *args], capture_output=True, text=True, check=True).stdout


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


status = git("status", "--porcelain=v1", "--untracked-files=all")
dirty = sorted(line[3:] for line in status.splitlines())
head_log = REPO / ".git/logs/HEAD"
OUT.write_text(json.dumps({
    "repo": str(REPO),
    "branch": git("symbolic-ref", "--short", "HEAD").strip(),
    "head": git("rev-parse", "HEAD").strip(),
    "main": git("rev-parse", "main").strip(),
    "branches": git("for-each-ref", "--format=%(refname:short)", "refs/heads").split(),
    "status": status,
    "dirty_files": {p: digest(REPO / p) for p in dirty},
    "env_file": digest(REPO / ".env"),
    "head_reflog_lines": len(head_log.read_text().splitlines()) if head_log.exists() else 0,
}, indent=2))
OUT.chmod(0o444)
