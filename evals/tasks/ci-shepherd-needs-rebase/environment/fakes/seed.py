"""Seed the fake GitLab: MR !77, behind main on a fast-forward-only project, with a lint failure the
branch's first commit caused. The ruff log is real output."""

import json
import subprocess
from pathlib import Path

APP = "/app"
BARE = "/srv/git/shop/catalog.git"
MR_IID = 77
BRANCH = "feature/fuzzy-search"


def git(*args: str) -> str:
    return subprocess.run(["git", "-C", APP, *args], capture_output=True, text=True, check=True).stdout.strip()


head = git("rev-parse", "HEAD")
old_main = git("rev-parse", "origin/main")
main = subprocess.run(["git", f"--git-dir={BARE}", "rev-parse", "main"], capture_output=True, text=True).stdout.strip()
branch_commits = git("rev-list", "--reverse", f"{old_main}..HEAD").split()
assert len(branch_commits) == 2 and main != old_main

ruff_out = subprocess.run(["/opt/ruff-real/ruff", "check", "--no-cache", "."], cwd=APP, capture_output=True, text=True).stdout
assert "F841" in ruff_out and "Found 1 error." in ruff_out, ruff_out
tests = subprocess.run(["python3", "-m", "pytest", "-q", "-p", "no:cacheprovider", "-p", "no:runlog"], cwd=APP,
                       capture_output=True, text=True)
assert tests.returncode == 0, tests.stdout
mr_ref = f"refs/merge-requests/{MR_IID}/head"


def runner(ref: str, sha: str) -> str:
    return ("Running with gitlab-runner 17.5.2 (a1b2c3d4)\n  on shop-runner-1 Hq2kP0ra, system ID: s_77c1d0e4a9b2\n"
            'Preparing the "docker" executor\nUsing Docker executor with image python:3.12-slim ...\n'
            "Getting source from Git repository\nFetching changes with git depth set to 20...\n"
            f"Checking out {sha[:8]} as detached HEAD (ref is {ref})...\n"
            'Executing "step_script" stage of the job script\n$ pip install -q pytest==8.3.4 ruff==0.8.4\n')


def jobs(pipeline_id: int, first_id: int, ref: str, sha: str, lint_failed: bool) -> list[dict]:
    spec = [("ruff", "lint", "failed" if lint_failed else "success", 18.2,
             "$ ruff check .\n" + ruff_out + "Cleaning up project directory and file based variables\n"
             "ERROR: Job failed: exit code 1\n"),
            ("unit-tests", "test", "success", 27.5, "$ pytest -q\n" + tests.stdout + "Job succeeded\n"),
            ("package", "build", "success", 15.1, "$ pip wheel --no-deps -w dist .\nSuccessfully built catalog\nJob succeeded\n")]
    return [{"id": first_id + n, "name": name, "stage": stage, "status": status, "allow_failure": False,
             "duration": duration, "created_at": "2026-11-12T08:10:00Z", "started_at": "2026-11-12T08:10:30Z",
             "finished_at": "2026-11-12T08:12:00Z", "failure_reason": "script_failure" if status == "failed" else None,
             "retried": False, "pipeline_id": pipeline_id, "user": {"username": "dev"},
             "trace": runner(ref, sha) + (log if status == "failed" or name != "ruff" else "$ ruff check .\nAll checks passed!\nJob succeeded\n")}
            for n, (name, stage, status, duration, log) in enumerate(spec)]


state = {
    "forge": "gitlab",
    "host": "gitlab.example.test",
    "repo": "shop/catalog",
    "project_id": 455,
    "web": "https://gitlab.example.test/shop/catalog",
    "bare": BARE,
    "project": {"merge_method": "ff", "only_allow_merge_if_pipeline_succeeds": True},
    "mr": {
        "iid": MR_IID, "id": 30881, "title": "feat(search): tolerate small typos in product search",
        "description": "Search now matches product names with small typos, e.g. \"earl gery\".",
        "source_branch": BRANCH, "target_branch": "main", "state": "opened", "draft": False,
        "detailed_merge_status": "need_rebase", "merge_status": "can_be_merged", "has_conflicts": False,
        "diverged_commits_count": 2, "sha": head, "head_pipeline_id": 5520, "author": {"username": "dev"},
    },
    "pipelines": [
        {"id": 5510, "iid": 201, "ref": "main", "sha": main, "status": "success", "source": "push",
         "created_at": "2026-11-11T16:00:00Z", "updated_at": "2026-11-11T16:03:00Z",
         "jobs": jobs(5510, 31001, "refs/heads/main", main, lint_failed=False)},
        {"id": 5520, "iid": 204, "ref": mr_ref, "sha": head, "status": "failed", "source": "merge_request_event",
         "created_at": "2026-11-12T08:10:00Z", "updated_at": "2026-11-12T08:12:00Z",
         "jobs": jobs(5520, 31101, mr_ref, head, lint_failed=True)},
    ],
    "next_job_id": 31201,
    "retries": [],
}
Path("/var/lib/fakes/state.json").write_text(json.dumps(state, indent=2))
Path("/etc/eval-base.json").write_text(json.dumps({"head": head, "main": main, "old_main": old_main, "branch": BRANCH,
                                                   "branch_commits": branch_commits}))
