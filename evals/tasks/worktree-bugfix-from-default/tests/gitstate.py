"""Shared git inspection helpers for the worktree-flow verifiers."""
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

BASE = json.loads(Path("/etc/eval-base.json").read_text())
REPO = Path(BASE["repo"])
KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def git(*args, cwd=REPO, check=True):
    return subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True, check=check).stdout


def is_ancestor(older, newer):
    return subprocess.run(["git", "-C", str(REPO), "merge-base", "--is-ancestor", older, newer]).returncode == 0


def new_branches():
    """Branches created during the task that carry commits not on main."""
    names = set(git("for-each-ref", "--format=%(refname:short)", "refs/heads").split()) - set(BASE["branches"])
    return sorted(b for b in names if git("rev-list", "--count", f"{BASE['main']}..{b}").strip() != "0")


def task_branch():
    branches = new_branches()
    assert len(branches) == 1, f"expected exactly one new branch with commits, found {branches}"
    return branches[0]


def worktrees():
    """[(path, branch-or-None)] from `git worktree list --porcelain`; the first entry is the main checkout."""
    entries, path, branch = [], None, None
    for line in git("worktree", "list", "--porcelain").splitlines() + [""]:
        if line.startswith("worktree "):
            path = Path(line.split(" ", 1)[1]).resolve()
        elif line.startswith("branch "):
            branch = line.split(" ", 1)[1].removeprefix("refs/heads/")
        elif not line and path is not None:
            entries.append((path, branch))
            path, branch = None, None
    return entries


def worktree_of(branch):
    for path, checked_out in worktrees()[1:]:
        if checked_out == branch:
            return path
    return None


def changed_paths(branch, base=None):
    return set(git("diff", "--name-only", base or BASE["main"], branch).split())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def export_branch(branch):
    """Check the branch out into a fresh temp dir, independent of where the agent's worktree lives."""
    target = Path(tempfile.mkdtemp(prefix="eval-branch-"))
    archive = subprocess.run(["git", "-C", str(REPO), "archive", branch], capture_output=True, check=True).stdout
    subprocess.run(["tar", "-x", "-C", str(target)], input=archive, check=True)
    return target


def run_pytest(where, *args):
    return subprocess.run(["python3", "-m", "pytest", "-q", "-p", "no:cacheprovider", *args],
                          cwd=where, capture_output=True, text=True)


def cleanup(path):
    shutil.rmtree(path, ignore_errors=True)


def assert_original_checkout_untouched():
    assert git("symbolic-ref", "--short", "HEAD").strip() == BASE["branch"], "original checkout switched branch"
    assert git("rev-parse", "HEAD").strip() == BASE["head"], "original checkout's HEAD moved"
    head_log = REPO / ".git/logs/HEAD"
    lines = len(head_log.read_text().splitlines()) if head_log.exists() else 0
    assert lines == BASE["head_reflog_lines"], "original checkout's HEAD was moved (checkout/stash/reset) during the task"


def assert_dirty_work_untouched():
    linked = [p for p, _ in worktrees()[1:]]

    def holds_worktree(line):
        path = (REPO / line[3:].rstrip("/")).resolve()
        return line.startswith("?? ") and any(path == w or path in w.parents for w in linked)

    status = "".join(line + "\n" for line in git("status", "--porcelain=v1", "--untracked-files=all").splitlines()
                     if not holds_worktree(line))
    assert status == BASE["status"], "uncommitted work changed"
    for rel, expected in BASE["dirty_files"].items():
        assert digest(REPO / rel) == expected, f"{rel} content changed"
    assert git("stash", "list").strip() == "", "work left in the stash"


def assert_in_linked_worktree(branch):
    """Branch is in a linked worktree, or its worktree was already cleaned up.

    A cleaned-up worktree is accepted only if the original checkout never moved: the HEAD
    reflog check catches stash/checkout-back flows that also leave the branch unchecked-out.
    Returns the worktree path, or None when it was removed.
    """
    path = worktree_of(branch)
    if path is None:
        checked_out = [b for _, b in worktrees()]
        assert branch not in checked_out, f"{branch} is checked out in the original checkout: {worktrees()}"
        assert_original_checkout_untouched()
    return path


def assert_not_nested(branch):
    path = worktree_of(branch)
    if path is None:
        return
    others = [p for p, b in worktrees() if b != branch]
    for other in others:
        assert other not in path.parents, f"worktree {path} is nested inside {other}"


def assert_based_on_main(branch, unmerged_branch):
    assert git("merge-base", branch, "main").strip() == BASE["main"] == git("rev-parse", "main").strip(), \
        "branch is not cut from the current main tip (or main itself moved)"
    assert not is_ancestor(git("rev-parse", unmerged_branch).strip(), branch), \
        f"{branch} stacks on unmerged {unmerged_branch}"


def assert_branch_convention(branch, prefix):
    assert branch.startswith(prefix), f"{branch} does not follow the {prefix}<slug> convention"
    slug = branch.removeprefix(prefix)
    assert KEBAB.match(slug) and len(slug) <= 40, f"slug {slug!r} is not short kebab-case"


def assert_worktree_dir_short_kebab(branch):
    path = worktree_of(branch)
    if path is None:
        return
    assert KEBAB.match(path.name) and len(path.name) <= 40, f"worktree dir {path.name!r} is not short kebab-case"


ORIGIN = "/app/origin.git"


def origin_sha(branch):
    out = subprocess.run(["git", "--git-dir", ORIGIN, "rev-parse", "--verify", "-q", f"refs/heads/{branch}"],
                         capture_output=True, text=True)
    return out.stdout.strip() or None


def assert_pushed(branch):
    sha = origin_sha(branch)
    assert sha is not None, f"{branch} was not pushed to origin"
    assert sha == git("rev-parse", branch).strip(), "origin has a different tip than the local branch"
    assert origin_sha("main") == BASE["main"], "origin/main was changed"
    return sha
