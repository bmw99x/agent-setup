"""Build /app's git history and the matching canned forge from a spec module.

    python3 build_history.py <spec.py>

The spec defines REPO, HOST, KIND ("gitlab" | "github"), PEOPLE {user: (name, email)} and
STEPS: a list of Commit (straight onto main) and MR (a branch merged with --no-ff, or
left open, in which case only the forge keeps its diff). Writes /opt/fakes/forge.json.
"""

import json
import os
import runpy
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

APP = Path("/app")
FORGE = Path("/opt/fakes/forge.json")


@dataclass
class Commit:
    author: str
    at: str
    message: str
    files: dict[str, str | None | Callable[[str], str]]


@dataclass
class Note:
    author: str
    at: str
    body: str
    path: str | None = None
    line: int | None = None


@dataclass
class MR:
    number: int
    author: str
    title: str
    description: str
    branch: str
    created_at: str
    commits: list[Commit]
    notes: list[Note] = field(default_factory=list)
    merged_at: str | None = None
    merged_by: str | None = None
    draft: bool = False


def _git(*args: str, env: dict | None = None) -> str:
    out = subprocess.run(["git", *args], cwd=APP, capture_output=True, text=True, env={**os.environ, **(env or {})})
    if out.returncode:
        sys.exit(f"git {' '.join(args)} failed: {out.stderr}")
    return out.stdout.strip()


def _ident(people: dict, user: str, at: str) -> dict:
    name, email = people[user]
    return {"GIT_AUTHOR_NAME": name, "GIT_AUTHOR_EMAIL": email, "GIT_AUTHOR_DATE": at,
            "GIT_COMMITTER_NAME": name, "GIT_COMMITTER_EMAIL": email, "GIT_COMMITTER_DATE": at}


def _apply(people: dict, c: Commit) -> str:
    for rel, content in c.files.items():
        p = APP / rel
        if content is None:
            p.unlink()
            continue
        if callable(content):
            content = content(p.read_text())
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
    _git("add", "-A")
    _git("commit", "-q", "-m", c.message, env=_ident(people, c.author, c.at))
    return _git("rev-parse", "HEAD")


def main(spec_path: str) -> None:
    spec = runpy.run_path(spec_path, init_globals={"Commit": Commit, "MR": MR, "Note": Note})
    people, kind, repo = spec["PEOPLE"], spec["KIND"], spec["REPO"]
    APP.mkdir(exist_ok=True)
    _git("init", "-q", "-b", "main")
    mrs, note_id = [], 1000
    for step in spec["STEPS"]:
        if isinstance(step, Commit):
            _apply(people, step)
            continue
        _git("checkout", "-q", "-b", step.branch)
        commits = []
        for c in step.commits:
            sha = _apply(people, c)
            commits.append({"sha": sha, "title": c.message.splitlines()[0], "author": c.author, "at": c.at})
        diff = _git("diff", "--no-color", f"main...{step.branch}") + "\n"
        _git("checkout", "-q", "main")
        merge_sha = None
        if step.merged_at:
            msg = (f"Merge branch '{step.branch}' into 'main'\n\n{step.title}\n\nSee merge request {repo}!{step.number}"
                   if kind == "gitlab" else f"Merge pull request #{step.number} from {repo.split('/')[0]}/{step.branch}\n\n{step.title}")
            _git("merge", "-q", "--no-ff", "-m", msg, step.branch, env=_ident(people, step.merged_by, step.merged_at))
            merge_sha = _git("rev-parse", "HEAD")
        _git("branch", "-q", "-D", step.branch)
        notes = []
        for n in step.notes:
            note_id += 1
            notes.append({"id": note_id, "author": n.author, "created_at": n.at, "body": n.body, "path": n.path, "line": n.line})
        last = max([step.created_at, *(n.at for n in step.notes), *(c.at for c in step.commits), step.merged_at or ""])
        mrs.append({
            "number": step.number, "title": step.title, "description": step.description,
            "state": "merged" if step.merged_at else "opened", "draft": step.draft, "author": step.author,
            "merged_by": step.merged_by, "created_at": step.created_at, "updated_at": last,
            "merged_at": step.merged_at, "source_branch": step.branch, "target_branch": "main",
            "merge_commit_sha": merge_sha, "commits": commits, "diff": diff, "notes": notes,
        })
    _git("remote", "add", "origin", f"git@{spec['HOST']}:{repo}.git")
    _git("update-ref", "refs/remotes/origin/main", "main")
    _git("symbolic-ref", "refs/remotes/origin/HEAD", "refs/remotes/origin/main")
    web = f"https://{spec['HOST']}/{repo}"
    FORGE.parent.mkdir(parents=True, exist_ok=True)
    FORGE.write_text(json.dumps({"kind": kind, "host": spec["HOST"], "repo": repo, "web": web,
                                 "people": {u: p[0] for u, p in people.items()}, "mrs": mrs}, indent=2))


if __name__ == "__main__":
    main(sys.argv[1])
