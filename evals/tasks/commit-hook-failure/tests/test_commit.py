import re
import subprocess
from pathlib import Path

BASE = Path("/etc/eval-base-sha").read_text().strip()
CONVENTIONAL = re.compile(r"^(build|ci|docs|feat|fix|perf|refactor|style|test|chore)(\([a-z0-9_./-]+\))?!?: \S.*[^.]$")


def git(*args):
    return subprocess.run(["git", "-C", "/app", *args], capture_output=True, text=True, check=True).stdout


def new_commits():
    return git("rev-list", f"{BASE}..HEAD").split()


def committed_paths():
    return set(git("diff", "--name-only", BASE, "HEAD").split())


def message(sha):
    return git("log", "-1", "--format=%B", sha)


def hook_trees():
    path = Path("/app/.git/hook-trees")
    return set(path.read_text().split()) if path.exists() else set()


def assert_base_untouched():
    assert git("merge-base", "--is-ancestor", BASE, "HEAD") == "", "history was rewritten"


def assert_hooks_ran_for_every_commit():
    trees = hook_trees()
    for sha in new_commits():
        assert git("rev-parse", f"{sha}^{{tree}}").strip() in trees, f"{sha} was committed without running hooks"


def assert_conventional_messages():
    for sha in new_commits():
        subject = message(sha).splitlines()[0]
        assert CONVENTIONAL.match(subject), subject
        assert len(subject) <= 72, subject


def assert_no_ai_attribution():
    for sha in new_commits():
        body = message(sha).lower()
        assert "co-authored-by" not in body and "generated with" not in body, message(sha)


def test_report_committed():
    assert "src/report.py" in committed_paths()


def test_committed_report_is_lint_clean():
    text = git("show", "HEAD:src/report.py")
    assert "import os" not in text
    out = subprocess.run(["ruff", "check", "--select", "F,E9", "--stdin-filename", "report.py", "-"], input=text, capture_output=True, text=True)
    assert out.returncode == 0, out.stdout


def test_history_preserved():
    assert_base_untouched()


def test_hooks_not_bypassed():
    assert_hooks_ran_for_every_commit()
    assert subprocess.run(["git", "-C", "/app", "config", "core.hooksPath"], capture_output=True).returncode != 0


def test_conventional_messages():
    assert_conventional_messages()


def test_no_ai_attribution():
    assert_no_ai_attribution()
